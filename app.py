import json
import os
import re
import shutil
import sqlite3
import tempfile
import unicodedata
import uuid
from datetime import datetime, timedelta
from contextlib import closing
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    has_request_context,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
DEMO_BASE_DATABASE = BASE_DIR / "diarias.db"
LOCALITIES_FILE = BASE_DIR / "static" / "localidades.js"
DEMO_BASE_UPLOAD_FOLDER = BASE_DIR / "uploads"
DEMO_ENVIRONMENTS_ROOT = Path(tempfile.gettempdir()) / "diaria_digital_demo"
DEMO_ENVIRONMENT_MAX_AGE = timedelta(days=7)
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "doc", "docx"}
ACCOUNTABILITY_ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
ACCOUNTABILITY_DEADLINE_DAYS = 2
# Regra operacional demonstrativa para o caso exatamente igual a 12h, nao definido expressamente na referencia legal usada no projeto.
EXACT_12_HOURS_DAILY_FRACTION = 0.70

app = Flask(__name__)
app.config["SECRET_KEY"] = "chave-academica-altere-em-producao"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

DEMO_REQUESTER_EMAIL = "solicitante@academico.test"
DEMO_VALIDATOR_EMAIL = "validador@academico.test"
DEMO_REQUESTER_CPF = "11111111111"
DEMO_VALIDATOR_CPF = "22222222222"
DEMO_CLEAR_REQUESTER_CPF = "33333333333"

DAILY_GROUPS = {
    "agente_politico_comissionado": "Prefeito Municipal, Vice-Prefeito, Vereadores e Secretários",
    "servidor_geral": "Demais servidores efetivos, contratados, temporários e cargos em comissão",
}

DAILY_RANGES = {
    "sc_ate_200": "Até 200 km dentro de Santa Catarina",
    "sc_acima_200": "Acima de 200 km dentro de Santa Catarina",
    "capital_sc_ou_fora_ate_1000": "Capital de SC ou fora do Estado até 1000 km",
    "capital_federal_ou_acima_1000": "Capital Federal ou acima de 1000 km",
}

DAILY_RATES = {
    "agente_politico_comissionado": {
        "sc_ate_200": 300.00,
        "sc_acima_200": 600.00,
        "capital_sc_ou_fora_ate_1000": 700.00,
        "capital_federal_ou_acima_1000": 1500.00,
    },
    "servidor_geral": {
        "sc_ate_200": 300.00,
        "sc_acima_200": 500.00,
        "capital_sc_ou_fora_ate_1000": 800.00,
        "capital_federal_ou_acima_1000": 1300.00,
    },
}

STATUS_LABELS = {
    "rascunho": "Rascunho",
    "enviada": "Enviada",
    "aprovada": "Viagem Aprovada",
    "correcao_solicitada": "Correção Solicitada",
    "corrigida": "Corrigida",
    "prestacao_enviada": "Prestação Enviada",
    "prestacao_correcao_solicitada": "Correção da Prestação Solicitada",
    "prestacao_corrigida": "Prestação Corrigida",
    "prestacao_aprovada": "Prestação Aprovada",
    "prestacao_aprovada_ressalvas": "Prestação Aprovada com Ressalvas",
    "rejeitada": "Rejeitada",
}

REQUEST_REVIEW_STATUSES = {"enviada", "corrigida", "correcao_solicitada", "aprovada"}
ACCOUNTABILITY_REVIEW_STATUSES = {"prestacao_enviada", "prestacao_corrigida"}

PROCESS_STAGES = [
    {
        "key": "solicitacao",
        "label": "Solicita\u00e7\u00e3o",
        "description": "Dados da viagem sao preenchidos e encaminhados para analise.",
    },
    {
        "key": "analise",
        "label": "An\u00e1lise",
        "description": "A solicitacao e conferida pelo servidor responsavel pela validacao.",
    },
    {
        "key": "viagem",
        "label": "Viagem",
        "description": "A solicitacao foi aprovada e o afastamento esta autorizado.",
    },
    {
        "key": "prestacao",
        "label": "Presta\u00e7\u00e3o de contas",
        "description": "O servidor apresenta as informacoes e os comprovantes referentes a viagem realizada.",
    },
    {
        "key": "conclusao",
        "label": "Conclus\u00e3o",
        "description": "A prestacao de contas foi analisada e o processo foi finalizado.",
    },
]

PROCESS_STAGE_BY_STATUS = {
    "rascunho": 0,
    "correcao_solicitada": 0,
    "enviada": 1,
    "corrigida": 1,
    "aprovada": 2,
    "prestacao_enviada": 3,
    "prestacao_corrigida": 3,
    "prestacao_correcao_solicitada": 3,
    "prestacao_aprovada": 4,
    "prestacao_aprovada_ressalvas": 4,
}

ROLE_LABELS = {
    "solicitante": "Servidor solicitante",
    "validador": "Servidor validador",
}


def normalize_cpf(cpf):
    return "".join(ch for ch in (cpf or "") if ch.isdigit())


def validate_cpf(cpf):
    normalized = normalize_cpf(cpf)
    # Versao demonstrativa: valida somente presenca/formato, sem digitos verificadores oficiais.
    if len(normalized) != 11:
        raise ValueError("Informe um CPF com 11 digitos.")
    return normalized


def format_cpf(cpf):
    digits = normalize_cpf(cpf)
    if len(digits) != 11:
        return cpf or ""
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def legacy_email_for_cpf(cpf):
    return f"{cpf}@cpf.local"


def is_valid_demo_environment_id(environment_id):
    return bool(re.fullmatch(r"[0-9a-f]{32}", environment_id or ""))


def get_demo_environment_folder(environment_id):
    if not is_valid_demo_environment_id(environment_id):
        raise ValueError("Identificador de ambiente demonstrativo invalido.")
    return DEMO_ENVIRONMENTS_ROOT / environment_id


def cleanup_old_demo_environments(current_environment_id=None):
    """Remove somente ambientes UUID sem utilizacao ha mais de 7 dias."""
    if not DEMO_ENVIRONMENTS_ROOT.exists():
        return
    cutoff = datetime.now().timestamp() - DEMO_ENVIRONMENT_MAX_AGE.total_seconds()
    for candidate in DEMO_ENVIRONMENTS_ROOT.iterdir():
        if (
            not candidate.is_dir()
            or candidate.is_symlink()
            or not is_valid_demo_environment_id(candidate.name)
            or candidate.name == current_environment_id
        ):
            continue
        try:
            if candidate.stat().st_mtime < cutoff:
                shutil.rmtree(candidate)
        except FileNotFoundError:
            pass


def copy_demo_base_uploads(database_path, upload_folder):
    """Copia apenas arquivos referenciados pelo banco-base, quando existirem."""
    if not DEMO_BASE_UPLOAD_FOLDER.is_dir():
        return
    with closing(sqlite3.connect(database_path)) as db:
        filenames = [row[0] for row in db.execute("SELECT filename FROM attachments")]
    for filename in filenames:
        safe_name = Path(filename).name
        if safe_name != filename:
            continue
        source = DEMO_BASE_UPLOAD_FOLDER / safe_name
        if source.is_file():
            shutil.copy2(source, upload_folder / safe_name)


def prepare_demo_scenarios(database_path):
    today = datetime.now().date()
    overdue_return = today - timedelta(days=3)
    overdue_departure = overdue_return - timedelta(days=1)
    with closing(sqlite3.connect(database_path)) as db, db:
        db.row_factory = sqlite3.Row
        overdue_user = db.execute(
            "SELECT id FROM users WHERE cpf = ?", (DEMO_REQUESTER_CPF,)
        ).fetchone()
        clear_user = db.execute(
            "SELECT id FROM users WHERE cpf = ?", (DEMO_CLEAR_REQUESTER_CPF,)
        ).fetchone()
        if overdue_user:
            scenario = db.execute(
                """
                SELECT id FROM requests
                WHERE user_id = ? AND status = 'aprovada'
                  AND (accountability_text IS NULL OR TRIM(accountability_text) = '')
                ORDER BY id DESC LIMIT 1
                """,
                (overdue_user["id"],),
            ).fetchone()
            now = datetime.now().isoformat(timespec="seconds")
            if scenario:
                db.execute(
                    """
                    UPDATE requests
                    SET departure_date = ?, return_date = ?, status = 'aprovada',
                        accountability_text = NULL, updated_at = ?
                    WHERE id = ?
                    """,
                    (overdue_departure.isoformat(), overdue_return.isoformat(), now, scenario["id"]),
                )
            else:
                db.execute(
                    """
                    INSERT INTO requests (
                        user_id, destination, departure_date, return_date, objective,
                        estimated_amount, status, accountability_text, created_at, updated_at,
                        daily_group, daily_range, has_overnight, departure_time, return_time,
                        distance_km, daily_factor, base_amount, overnight_count, daily_quantity
                    ) VALUES (?, ?, ?, ?, ?, ?, 'aprovada', NULL, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        overdue_user["id"], "Florianopolis - SC",
                        overdue_departure.isoformat(), overdue_return.isoformat(),
                        "Cenario demonstrativo de prestacao de contas", 800.0, now, now,
                        "servidor_geral", "capital_sc_ou_fora_ate_1000", "08:00", "18:00",
                        320.0, 1.0, 800.0, 1, 1.0,
                    ),
                )
        if clear_user:
            # Mantem eventuais viagens-base, mas impede que comecem vencidas.
            db.execute(
                """
                UPDATE requests SET return_date = ?, updated_at = ?
                WHERE user_id = ? AND return_date <= ? AND (
                    (status = 'aprovada' AND (accountability_text IS NULL OR TRIM(accountability_text) = ''))
                    OR status = 'prestacao_correcao_solicitada'
                )
                """,
                (today.isoformat(), datetime.now().isoformat(timespec="seconds"),
                 clear_user["id"], (today - timedelta(days=2)).isoformat()),
            )


def create_demo_environment(environment_id):
    if not DEMO_BASE_DATABASE.is_file():
        raise RuntimeError("Banco-base da demonstracao nao encontrado.")
    DEMO_ENVIRONMENTS_ROOT.mkdir(parents=True, exist_ok=True)
    cleanup_old_demo_environments(environment_id)
    environment_folder = get_demo_environment_folder(environment_id)
    environment_folder.mkdir(exist_ok=True)
    upload_folder = environment_folder / "uploads"
    upload_folder.mkdir(exist_ok=True)
    database_path = environment_folder / "diarias.db"
    temporary_database = environment_folder / "diarias.db.preparing"
    shutil.copy2(DEMO_BASE_DATABASE, temporary_database)
    init_db(temporary_database)
    prepare_demo_scenarios(temporary_database)
    copy_demo_base_uploads(temporary_database, upload_folder)
    temporary_database.replace(database_path)
    return database_path


def get_demo_environment_id():
    if not has_request_context():
        raise RuntimeError("O ambiente demonstrativo exige um contexto de requisicao.")
    session.permanent = True
    environment_id = session.get("demo_environment_id")
    if not is_valid_demo_environment_id(environment_id):
        environment_id = uuid.uuid4().hex
        session["demo_environment_id"] = environment_id
    return environment_id


def get_demo_database_path():
    environment_id = get_demo_environment_id()
    environment_folder = get_demo_environment_folder(environment_id)
    database_path = environment_folder / "diarias.db"
    if not database_path.is_file():
        create_demo_environment(environment_id)
    os.utime(environment_folder, None)
    return database_path


def get_demo_upload_folder():
    database_path = get_demo_database_path()
    upload_folder = database_path.parent / "uploads"
    upload_folder.mkdir(exist_ok=True)
    return upload_folder


def get_db(database_path=None):
    path = Path(database_path) if database_path is not None else get_demo_database_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(database_path):
    with closing(get_db(database_path)) as db, db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                cpf TEXT,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('solicitante', 'validador')),
                daily_group TEXT
            );

            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                destination TEXT NOT NULL,
                departure_date TEXT NOT NULL,
                return_date TEXT NOT NULL,
                objective TEXT NOT NULL,
                estimated_amount REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'rascunho',
                validator_comment TEXT,
                accountability_text TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                original_name TEXT NOT NULL,
                kind TEXT NOT NULL CHECK(kind IN ('solicitacao', 'prestacao')),
                uploaded_at TEXT NOT NULL,
                FOREIGN KEY(request_id) REFERENCES requests(id)
            );
            """
        )

        existing_user_columns = {
            row["name"] for row in db.execute("PRAGMA table_info(users)").fetchall()
        }
        if "daily_group" not in existing_user_columns:
            db.execute("ALTER TABLE users ADD COLUMN daily_group TEXT")
        user_columns_to_add = {
            "cpf": "TEXT",
            "registration": "TEXT",
            "public_position": "TEXT",
        }
        for column_name, column_definition in user_columns_to_add.items():
            if column_name not in existing_user_columns:
                db.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_definition}")

        existing_columns = {
            row["name"] for row in db.execute("PRAGMA table_info(requests)").fetchall()
        }
        columns_to_add = {
            "daily_group": "TEXT",
            "daily_range": "TEXT",
            "has_overnight": "INTEGER DEFAULT 1",
            "accountability_departure_time": "TEXT",
            "accountability_arrival_time": "TEXT",
            "transport_mode": "TEXT",
            "departure_km": "REAL",
            "arrival_km": "REAL",
            "refund_amount": "REAL DEFAULT 0",
            "departure_time": "TEXT",
            "return_time": "TEXT",
            "distance_km": "REAL",
            "daily_factor": "REAL",
            "base_amount": "REAL",
            "overnight_count": "INTEGER DEFAULT 0",
            "daily_quantity": "REAL",
        }
        for column_name, column_definition in columns_to_add.items():
            if column_name not in existing_columns:
                db.execute(f"ALTER TABLE requests ADD COLUMN {column_name} {column_definition}")

        existing_attachment_columns = {
            row["name"] for row in db.execute("PRAGMA table_info(attachments)").fetchall()
        }
        if "attachment_type" not in existing_attachment_columns:
            db.execute("ALTER TABLE attachments ADD COLUMN attachment_type TEXT")

        user_count = db.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
        if user_count == 0:
            db.executemany(
                """
                INSERT INTO users (name, email, cpf, password_hash, role, daily_group, registration, public_position)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        "Servidor Solicitante",
                        DEMO_REQUESTER_EMAIL,
                        DEMO_REQUESTER_CPF,
                        generate_password_hash("123456"),
                        "solicitante",
                        "servidor_geral",
                        "0001",
                        "Servidor Público",
                    ),
                    (
                        "Servidor Validador",
                        DEMO_VALIDATOR_EMAIL,
                        DEMO_VALIDATOR_CPF,
                        generate_password_hash("123456"),
                        "validador",
                        None,
                        None,
                        None,
                    ),
                ],
            )
        else:
            db.execute(
                """
                UPDATE users
                SET daily_group = COALESCE(daily_group, 'servidor_geral'),
                    registration = COALESCE(registration, '0001'),
                    public_position = COALESCE(public_position, 'Servidor Público')
                WHERE role = 'solicitante'
                """
            )
            db.execute(
                """
                UPDATE users
                SET daily_group = 'servidor_geral'
                WHERE daily_group = 'agente_politico_comissionado'
                  AND role = 'solicitante'
                  AND LOWER(COALESCE(public_position, '')) LIKE '%comission%'
                  AND LOWER(COALESCE(public_position, '')) NOT LIKE '%secret%'
                  AND LOWER(COALESCE(public_position, '')) NOT LIKE '%prefeit%'
                  AND LOWER(COALESCE(public_position, '')) NOT LIKE '%vereador%'
                """
            )
            db.execute(
                """
                UPDATE users
                SET cpf = ?, password_hash = ?
                WHERE email = ? OR (role = 'solicitante' AND name = 'Servidor Solicitante')
                """,
                (DEMO_REQUESTER_CPF, generate_password_hash("123456"), DEMO_REQUESTER_EMAIL),
            )
            db.execute(
                """
                UPDATE users
                SET cpf = ?, password_hash = ?
                WHERE email = ? OR (role = 'validador' AND name = 'Servidor Validador')
                """,
                (DEMO_VALIDATOR_CPF, generate_password_hash("123456"), DEMO_VALIDATOR_EMAIL),
            )

        users_without_cpf = db.execute(
            "SELECT id FROM users WHERE cpf IS NULL OR TRIM(cpf) = ''"
        ).fetchall()
        for row in users_without_cpf:
            generated_cpf = f"{90000000000 + row['id']:011d}"
            db.execute("UPDATE users SET cpf = ? WHERE id = ?", (generated_cpf, row["id"]))

        db.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_cpf "
            "ON users(cpf) WHERE cpf IS NOT NULL AND cpf != ''"
        )

        demo_users = [
            ("Solicitante com prestacao em atraso", DEMO_REQUESTER_CPF, "solicitante", "servidor_geral", "0001", "Servidor Publico"),
            ("Servidor Validador", DEMO_VALIDATOR_CPF, "validador", None, "0002", "Servidor Validador"),
            ("Servidor solicitante sem pendencia", DEMO_CLEAR_REQUESTER_CPF, "solicitante", "agente_politico_comissionado", "0003", "Empregado publico"),
        ]
        for name, cpf, role, daily_group, registration, public_position in demo_users:
            existing_demo_user = db.execute(
                "SELECT id FROM users WHERE cpf = ?", (cpf,)
            ).fetchone()
            if existing_demo_user:
                db.execute(
                    """
                    UPDATE users SET password_hash = ?, role = ?, daily_group = ?,
                        registration = COALESCE(registration, ?),
                        public_position = COALESCE(public_position, ?)
                    WHERE id = ?
                    """,
                    (generate_password_hash("123456"), role, daily_group,
                     registration, public_position, existing_demo_user["id"]),
                )
            else:
                db.execute(
                    """
                    INSERT INTO users (name, email, cpf, password_hash, role, daily_group, registration, public_position)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (name, legacy_email_for_cpf(cpf), cpf, generate_password_hash("123456"),
                     role, daily_group, registration, public_position),
                )


def current_user():
    if "user_id" not in session:
        return None
    with closing(get_db()) as db, db:
        return db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()


@app.template_filter("cpf_br")
def cpf_br_filter(value):
    return format_cpf(value)


@app.context_processor
def inject_user():
    return {
        "current_user": current_user(),
        "daily_groups": DAILY_GROUPS,
        "daily_ranges": DAILY_RANGES,
        "status_labels": STATUS_LABELS,
        "role_labels": ROLE_LABELS,
    }


def load_locality_distances():
    if not LOCALITIES_FILE.exists():
        return {}
    source = LOCALITIES_FILE.read_text(encoding="utf-8")
    match = re.search(r"const\s+distanciasLocalidadesKm\s*=\s*(\{.*?\});", source, re.S)
    if not match:
        return {}
    js_object = re.sub(r"//.*", "", match.group(1))
    js_object = re.sub(r",\s*}", "}", js_object)
    try:
        return json.loads(js_object)
    except json.JSONDecodeError:
        return {}


def locality_key(state, city):
    return f"{state}|{city}"


def normalize_name(value):
    normalized = unicodedata.normalize("NFD", value or "")
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn").lower()


def is_state_capital(state, city):
    return state == "SC" and normalize_name(city) == "florianopolis"


def is_federal_capital(state, city):
    return state == "DF" and normalize_name(city) == "brasilia"


def get_destination_distance(state, city):
    distances = load_locality_distances()
    value = distances.get(locality_key(state, city))
    if value is None:
        return None
    return float(value)


def determine_daily_range(state, city, distance_km):
    if is_federal_capital(state, city):
        return "capital_federal_ou_acima_1000"
    if is_state_capital(state, city):
        return "capital_sc_ou_fora_ate_1000"
    if distance_km is None:
        raise ValueError("A distância rodoviária do município selecionado ainda não foi cadastrada.")
    if distance_km > 1000:
        return "capital_federal_ou_acima_1000"
    if state == "SC":
        return "sc_ate_200" if distance_km <= 200 else "sc_acima_200"
    return "capital_sc_ou_fora_ate_1000"


def parse_destination(destination):
    if not destination or " - " not in destination:
        return "", ""
    city, state = destination.rsplit(" - ", 1)
    return state, city


def parse_form_date(value):
    value = (value or "").strip()
    for date_format in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, date_format).date().isoformat()
        except ValueError:
            continue
    raise ValueError("Data inválida. Use o formato DD/MM/AA.")


def parse_form_time(value, field_label):
    value = (value or "").strip()
    try:
        datetime.strptime(value, "%H:%M")
    except ValueError:
        raise ValueError(f"Informe {field_label} no formato 24 horas HH:MM.")
    return value


def build_travel_datetimes(departure_date, departure_time, return_date, return_time):
    departure = datetime.fromisoformat(f"{departure_date}T{departure_time}")
    return_ = datetime.fromisoformat(f"{return_date}T{return_time}")
    return departure, return_


def validate_travel_period(departure_date, departure_time, return_date, return_time):
    departure, return_ = build_travel_datetimes(
        departure_date,
        departure_time,
        return_date,
        return_time,
    )
    today = datetime.now().date()

    if departure.date() < today:
        raise ValueError("A data de saída não pode ser anterior à data de hoje.")
    if return_ <= departure:
        raise ValueError("O retorno não pode ocorrer antes ou no mesmo momento da saída.")
    return (return_ - departure).total_seconds() / 3600


def calculate_max_overnights(departure_date, return_date):
    departure = datetime.fromisoformat(departure_date).date()
    return_ = datetime.fromisoformat(return_date).date()
    return max((return_ - departure).days, 0)


def validate_overnight_count(raw_value, departure_date, return_date):
    value = (raw_value if raw_value not in (None, "") else "0")
    value = str(value).strip()
    if not re.fullmatch(r"\d+", value):
        raise ValueError("Informe a quantidade de pernoites como numero inteiro maior ou igual a zero.")

    overnight_count = int(value)
    max_overnights = calculate_max_overnights(departure_date, return_date)
    if overnight_count > max_overnights:
        raise ValueError(f"A quantidade de pernoites nao pode ser maior que {max_overnights} para o periodo informado.")
    if max_overnights == 0 and overnight_count > 0:
        raise ValueError("Viagens com saida e retorno no mesmo dia devem ter zero pernoites.")
    return overnight_count


def calculate_residual_daily_fraction(residual_hours, has_residual_overnight):
    if residual_hours <= 0:
        return 0.0
    if has_residual_overnight:
        return 1.0
    if residual_hours > 12:
        return 0.70
    if residual_hours < 12:
        return 0.50
    # Decisao operacional demonstrativa: o caso exatamente 12h nao esta definido no trecho legal usado.
    return EXACT_12_HOURS_DAILY_FRACTION


def calculate_daily_quantity(duration_hours, overnight_count):
    """
    Regra operacional demonstrativa para multiplas diarias.

    A referencia legal do projeto define fracoes para periodos simples, mas nao detalha
    decomposicao de afastamentos com varios dias. Por isso, a versao demonstrativa
    separa blocos completos de 24h e calcula eventual periodo residual de forma isolada.
    """
    full_24h_blocks = int(duration_hours // 24)
    residual_hours = duration_hours - (full_24h_blocks * 24)
    has_residual_overnight = overnight_count > full_24h_blocks
    return full_24h_blocks + calculate_residual_daily_fraction(
        residual_hours,
        has_residual_overnight,
    )


def calculate_daily_amount(daily_group, daily_range, daily_quantity):
    base_amount = DAILY_RATES.get(daily_group, {}).get(daily_range)
    if base_amount is None:
        raise ValueError("Enquadramento de diaria invalido.")
    return base_amount, base_amount * daily_quantity


def get_overdue_accountability(user_id):
    deadline_date = (datetime.now().date() - timedelta(days=ACCOUNTABILITY_DEADLINE_DAYS)).isoformat()
    with closing(get_db()) as db, db:
        return db.execute(
            """
            SELECT *
            FROM requests
            WHERE user_id = ?
            AND return_date <= ?
            AND (
                (status = 'aprovada' AND (accountability_text IS NULL OR TRIM(accountability_text) = ''))
                OR status = 'prestacao_correcao_solicitada'
            )
            ORDER BY return_date ASC
            LIMIT 1
            """,
            (user_id, deadline_date),
        ).fetchone()


def calculate_request_amount(user, form):
    daily_group = user["daily_group"]

    if daily_group not in DAILY_RATES:
        raise ValueError("Seu usuario nao possui grupo de diaria cadastrado. Procure o validador.")

    destination = form.get("destination", "").strip()
    state, city = parse_destination(destination)
    if not state or not city:
        raise ValueError("Selecione o municipio de destino.")

    departure_date = parse_form_date(form["departure_date"])
    return_date = parse_form_date(form["return_date"])
    departure_time = parse_form_time(form.get("departure_time"), "a hora de saida")
    return_time = parse_form_time(form.get("return_time"), "a hora prevista de retorno")
    duration_hours = validate_travel_period(
        departure_date,
        departure_time,
        return_date,
        return_time,
    )
    overnight_count = validate_overnight_count(
        form.get("overnight_count", form.get("has_overnight", "0")),
        departure_date,
        return_date,
    )
    distance_km = get_destination_distance(state, city)
    daily_range = determine_daily_range(state, city, distance_km)
    daily_quantity = calculate_daily_quantity(duration_hours, overnight_count)
    base_amount, estimated_amount = calculate_daily_amount(
        daily_group,
        daily_range,
        daily_quantity,
    )

    return {
        "daily_group": daily_group,
        "daily_range": daily_range,
        "has_overnight": overnight_count > 0,
        "overnight_count": overnight_count,
        "departure_date": departure_date,
        "return_date": return_date,
        "departure_time": departure_time,
        "return_time": return_time,
        "distance_km": distance_km,
        "daily_factor": daily_quantity,
        "daily_quantity": daily_quantity,
        "base_amount": base_amount,
        "estimated_amount": estimated_amount,
        "duration_hours": duration_hours,
    }


def request_form_context(user, daily_request=None):
    initial_state = ""
    initial_city = ""
    if daily_request:
        initial_state, initial_city = parse_destination(daily_request["destination"])

    return {
        "user_daily_group": user["daily_group"],
        "daily_request": daily_request,
        "initial_state": initial_state,
        "initial_city": initial_city,
        "form_action": (
            url_for("edit_request", request_id=daily_request["id"])
            if daily_request
            else url_for("new_request")
        ),
        "form_title": "Corrigir solicitação" if daily_request else "Nova solicitação",
        "form_description": (
            "Revise os dados apontados pelo validador e encaminhe novamente."
            if daily_request
            else "Informe os dados básicos da viagem e anexe documentos de suporte."
        ),
        "submit_label": "Reenviar solicitação" if daily_request else "Enviar solicitação",
    }


@app.template_filter("date_br")
def date_br(value):
    if not value:
        return ""
    return datetime.fromisoformat(value).strftime("%d/%m/%y")


@app.template_filter("datetime_br")
def datetime_br(value):
    if not value:
        return ""
    return datetime.fromisoformat(value).strftime("%d/%m/%y %H:%M")


@app.template_filter("moeda_br")
def moeda_br(value):
    amount = float(value or 0)
    formatted = f"{amount:,.2f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


@app.template_filter("decimal_br")
def decimal_br(value, places=1):
    if value is None:
        return "-"
    return f"{float(value):.{places}f}".replace(".", ",")


@app.template_filter("daily_quantity_br")
def daily_quantity_br(value):
    quantity = float(value or 0)
    label = "diaria" if abs(quantity - 1.0) < 0.001 else "diarias"
    return f"{quantity:.2f}".replace(".", ",") + f" {label}"


@app.template_filter("duration_br")
def duration_br(daily_request):
    if not daily_request["departure_time"] or not daily_request["return_time"]:
        return "-"
    departure, return_ = build_travel_datetimes(
        daily_request["departure_date"],
        daily_request["departure_time"],
        daily_request["return_date"],
        daily_request["return_time"],
    )
    total_minutes = int((return_ - departure).total_seconds() // 60)
    if total_minutes < 0:
        return "-"
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours}h{minutes:02d}min"


@app.template_filter("status_label")
def status_label(value):
    return STATUS_LABELS.get(value, str(value).replace("_", " ").title())


@app.template_filter("status_class")
def status_class(value):
    return f"status-{str(value).replace('_', '-')}"


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if current_user() is None:
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            user = current_user()
            if user is None:
                return redirect(url_for("login"))
            if user["role"] != role:
                abort(403)
            return view(**kwargs)

        return wrapped_view

    return decorator


def get_process_progress(status):
    is_rejected = status == "rejeitada"
    current_index = PROCESS_STAGE_BY_STATUS.get(status, 0)
    is_complete = status in {"prestacao_aprovada", "prestacao_aprovada_ressalvas"}

    stages = []
    for index, stage in enumerate(PROCESS_STAGES):
        if is_rejected:
            state = "interrompida" if index == current_index else ("concluida" if index < current_index else "futura")
        elif is_complete:
            state = "concluida"
        elif index < current_index:
            state = "concluida"
        elif index == current_index:
            state = "atual"
        else:
            state = "futura"

        stages.append({
            **stage,
            "state": state,
            "index": index,
        })

    current_stage = PROCESS_STAGES[current_index]
    return {
        "stages": stages,
        "current_stage": current_stage,
        "current_index": current_index,
        "is_rejected": is_rejected,
        "is_complete": is_complete,
    }


def get_user_or_404(user_id):
    with closing(get_db()) as db, db:
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        abort(404)
    return user


def validate_user_form(form, user_id=None, password_required=False):
    name = form.get("name", "").strip()
    registration = form.get("registration", "").strip()
    public_position = form.get("public_position", "").strip()
    cpf = validate_cpf(form.get("cpf", ""))
    password = form.get("password", "")

    if not name:
        raise ValueError("Informe o nome.")
    if not registration:
        raise ValueError("Informe a matricula.")
    if not public_position:
        raise ValueError("Informe o cargo, emprego ou funcao.")
    if password_required and not password:
        raise ValueError("Informe a senha.")
    if password and len(password) < 6:
        raise ValueError("A senha deve ter ao menos 6 caracteres.")

    with closing(get_db()) as db, db:
        existing = db.execute(
            "SELECT id FROM users WHERE cpf = ? AND (? IS NULL OR id != ?)",
            (cpf, user_id, user_id),
        ).fetchone()
    if existing:
        raise ValueError("Ja existe usuario cadastrado com este CPF.")

    return {
        "name": name,
        "registration": registration,
        "public_position": public_position,
        "cpf": cpf,
        "password": password,
    }


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_file_for(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def save_attachment(file_storage, request_id, kind, attachment_type=None, allowed_extensions=None):
    if not file_storage or file_storage.filename == "":
        return
    allowed_extensions = allowed_extensions or ALLOWED_EXTENSIONS
    if not allowed_file_for(file_storage.filename, allowed_extensions):
        flash("Arquivo ignorado: formato não permitido.", "warning")
        return

    original_name = file_storage.filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    filename = f"{request_id}_{kind}_{timestamp}_{secure_filename(original_name)}"
    file_storage.save(get_demo_upload_folder() / filename)

    with closing(get_db()) as db, db:
        db.execute(
            """
            INSERT INTO attachments (request_id, filename, original_name, kind, attachment_type, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                filename,
                original_name,
                kind,
                attachment_type,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def get_request_or_404(request_id):
    with closing(get_db()) as db, db:
        daily_request = db.execute(
            """
            SELECT r.*, u.name AS requester_name, u.cpf AS requester_cpf,
                   u.registration AS requester_registration,
                   u.public_position AS requester_position
            FROM requests r
            JOIN users u ON u.id = r.user_id
            WHERE r.id = ?
            """,
            (request_id,),
        ).fetchone()
    if daily_request is None:
        abort(404)
    return daily_request


def user_can_view(daily_request):
    user = current_user()
    return user["role"] == "validador" or daily_request["user_id"] == user["id"]


def accountability_form_context(daily_request, attachments=None):
    attachments = attachments or []
    displacement_attachments = [
        item for item in attachments if item["attachment_type"] == "deslocamento"
    ]
    objective_attachments = [
        item for item in attachments if item["attachment_type"] == "objetivo"
    ]
    return {
        "daily_request": daily_request,
        "displacement_attachments": displacement_attachments,
        "objective_attachments": objective_attachments,
        "transport_modes": ["Aéreo", "Coletivo Rodoviário", "Veículo próprio", "Veículo oficial"],
    }


def get_attachments(request_id):
    with closing(get_db()) as db, db:
        return db.execute(
            "SELECT * FROM attachments WHERE request_id = ? ORDER BY uploaded_at DESC",
            (request_id,),
        ).fetchall()


def validate_accountability_files(existing_count, files, label):
    selected_files = [file for file in files if file and file.filename]
    total = existing_count + len(selected_files)
    if total < 1:
        raise ValueError(f"Anexe ao menos 1 comprovante de {label}.")
    if total > 10:
        raise ValueError(f"Anexe no máximo 10 comprovantes de {label}.")
    for file in selected_files:
        if not allowed_file_for(file.filename, ACCOUNTABILITY_ALLOWED_EXTENSIONS):
            raise ValueError(f"Comprovante de {label} deve ser PDF ou foto.")
    return selected_files


def validate_accountability_form(form, displacement_files, objective_files, attachments):
    refund_amount = float(form.get("refund_amount") or 0)
    received_amount = float(form.get("received_amount") or 0)

    if refund_amount < 0:
        raise ValueError("O valor a devolver não pode ser menor que zero.")
    if refund_amount > received_amount:
        raise ValueError("O valor a devolver não pode ser maior que o valor recebido.")
    if not form.get("accountability_text", "").strip():
        raise ValueError("Informe o resumo da prestação de contas.")
    if refund_amount == received_amount:
        return ([], [])

    departure_time = form.get("accountability_departure_time", "").strip()
    arrival_time = form.get("accountability_arrival_time", "").strip()

    if not departure_time:
        raise ValueError("Informe a hora de saída.")
    if not arrival_time:
        raise ValueError("Informe a hora de chegada.")
    for time_value in (departure_time, arrival_time):
        try:
            datetime.strptime(time_value, "%H:%M")
        except ValueError:
            raise ValueError("Informe os horários no formato 24 horas HH:MM.")

    if not form.get("transport_mode"):
        raise ValueError("Selecione o meio de transporte utilizado.")

    if form["transport_mode"] == "Veículo oficial":
        if not form.get("departure_km") or not form.get("arrival_km"):
            raise ValueError("Informe o KM de saída e o KM de chegada do veículo oficial.")
        if float(form["arrival_km"]) < float(form["departure_km"]):
            raise ValueError("O KM de chegada não pode ser menor que o KM de saída.")

    existing_displacement = len([item for item in attachments if item["attachment_type"] == "deslocamento"])
    existing_objective = len([item for item in attachments if item["attachment_type"] == "objetivo"])
    return (
        validate_accountability_files(existing_displacement, displacement_files, "deslocamento"),
        validate_accountability_files(existing_objective, objective_files, "cumprimento do objetivo"),
    )


@app.route("/")
def index():
    user = current_user()
    if user is None:
        return render_template("index.html")
    if user["role"] == "validador":
        return redirect(url_for("validator_dashboard"))
    return redirect(url_for("requester_dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        cpf = normalize_cpf(request.form.get("cpf", ""))
        password = request.form["password"]

        if len(cpf) != 11:
            flash("Informe um CPF com 11 digitos.", "danger")
            return render_template("login.html")

        with closing(get_db()) as db, db:
            user = db.execute("SELECT * FROM users WHERE cpf = ?", (cpf,)).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            environment_id = session.get("demo_environment_id")
            session.clear()
            session.permanent = True
            session["demo_environment_id"] = environment_id
            session["user_id"] = user["id"]
            flash("Login realizado com sucesso.", "success")
            return redirect(url_for("index"))

        flash("CPF ou senha invalidos.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Sessão encerrada.", "info")
    return redirect(url_for("login"))


@app.route("/reiniciar-demonstracao", methods=["POST"])
def reset_demo_environment():
    environment_id = session.get("demo_environment_id")
    if is_valid_demo_environment_id(environment_id):
        environment_folder = get_demo_environment_folder(environment_id)
        if environment_folder.is_dir() and not environment_folder.is_symlink():
            shutil.rmtree(environment_folder)
    session.clear()
    flash("Ambiente de demonstracao reiniciado com sucesso.", "success")
    return redirect(url_for("login"))


@app.route("/perfil")
@login_required
def profile():
    if current_user()["role"] != "validador":
        flash("Acesso ao cadastro restrito ao validador.", "warning")
        return redirect(url_for("index"))
    return redirect(url_for("edit_user", user_id=current_user()["id"]))


@app.route("/usuarios")
@role_required("validador")
def users_list():
    search = request.args.get("q", "").strip()
    role_filter = request.args.get("role", "")
    filters = []
    params = []

    if role_filter:
        filters.append("role = ?")
        params.append(role_filter)
    if search:
        normalized_search = normalize_cpf(search)
        filters.append("(name LIKE ? OR registration LIKE ? OR cpf LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%", f"%{normalized_search or search}%"])

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    with closing(get_db()) as db, db:
        users = db.execute(
            f"SELECT * FROM users {where_clause} ORDER BY name",
            params,
        ).fetchall()

    return render_template(
        "users_list.html",
        users=users,
        search=search,
        selected_role=role_filter,
    )


@app.route("/usuarios/novo", methods=["GET", "POST"])
@role_required("validador")
def new_user():
    if request.method == "POST":
        try:
            data = validate_user_form(request.form, password_required=True)
            role = request.form.get("role", "")
            if role not in ROLE_LABELS:
                raise ValueError("Selecione um perfil válido.")
            daily_group = request.form.get("daily_group") if role == "solicitante" else None
            if role == "solicitante" and daily_group not in DAILY_GROUPS:
                raise ValueError("Selecione o grupo de diária do solicitante.")
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("user_form.html", user=None, form_action=url_for("new_user"))

        with closing(get_db()) as db, db:
            db.execute(
                """
                INSERT INTO users (
                    name, registration, public_position, email, cpf,
                    password_hash, role, daily_group
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["name"],
                    data["registration"],
                    data["public_position"],
                    legacy_email_for_cpf(data["cpf"]),
                    data["cpf"],
                    generate_password_hash(data["password"]),
                    role,
                    daily_group,
                ),
            )

        flash("Usuário cadastrado com sucesso.", "success")
        return redirect(url_for("users_list"))

    return render_template("user_form.html", user=None, form_action=url_for("new_user"))


@app.route("/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
@role_required("validador")
def edit_user(user_id):
    logged_user = current_user()
    target_user = get_user_or_404(user_id)
    can_manage_users = logged_user["role"] == "validador"
    is_own_profile = logged_user["id"] == target_user["id"]

    if request.method == "POST":
        try:
            data = validate_user_form(request.form, user_id=user_id)
            role = target_user["role"]
            daily_group = target_user["daily_group"]
            if can_manage_users and not is_own_profile:
                role = request.form.get("role", "")
                if role not in ROLE_LABELS:
                    raise ValueError("Selecione um perfil válido.")
                daily_group = request.form.get("daily_group") if role == "solicitante" else None
                if role == "solicitante" and daily_group not in DAILY_GROUPS:
                    raise ValueError("Selecione o grupo de diária do solicitante.")
        except ValueError as error:
            flash(str(error), "danger")
            return render_template(
                "user_form.html",
                user=target_user,
                form_action=url_for("edit_user", user_id=user_id),
            )

        with closing(get_db()) as db, db:
            db.execute(
                """
                UPDATE users
                SET name = ?, registration = ?, public_position = ?,
                    cpf = ?, role = ?, daily_group = ?
                WHERE id = ?
                """,
                (
                    data["name"],
                    data["registration"],
                    data["public_position"],
                    data["cpf"],
                    role,
                    daily_group,
                    user_id,
                ),
            )
            if data["password"]:
                db.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (generate_password_hash(data["password"]), user_id),
                )

        flash("Cadastro atualizado com sucesso.", "success")
        if can_manage_users and not is_own_profile:
            return redirect(url_for("users_list"))
        return redirect(url_for("index"))

    return render_template(
        "user_form.html",
        user=target_user,
        form_action=url_for("edit_user", user_id=user_id),
    )


@app.route("/solicitante")
@role_required("solicitante")
def requester_dashboard():
    user = current_user()
    overdue_accountability = get_overdue_accountability(user["id"])
    status_filter = request.args.get("status", "")
    search = request.args.get("q", "").strip()
    filters = ["user_id = ?"]
    params = [user["id"]]

    if status_filter:
        filters.append("status = ?")
        params.append(status_filter)
    if search:
        filters.append("destination LIKE ?")
        params.append(f"%{search}%")

    where_clause = " AND ".join(filters)
    with closing(get_db()) as db, db:
        requests = db.execute(
            f"SELECT * FROM requests WHERE {where_clause} ORDER BY created_at DESC",
            params,
        ).fetchall()
    return render_template(
        "requester_dashboard.html",
        requests=requests,
        overdue_accountability=overdue_accountability,
        selected_status=status_filter,
        search=search,
    )


@app.route("/solicitacoes/nova", methods=["GET", "POST"])
@role_required("solicitante")
def new_request():
    user = current_user()
    overdue_accountability = get_overdue_accountability(user["id"])
    if overdue_accountability:
        flash(
            "Você possui prestação de contas pendente há mais de 48 horas e não pode criar nova solicitação.",
            "danger",
        )
        return redirect(url_for("request_detail", request_id=overdue_accountability["id"]))

    if request.method == "POST":
        try:
            calculated = calculate_request_amount(user, request.form)
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("request_form.html", **request_form_context(user))

        now = datetime.now().isoformat(timespec="seconds")
        with closing(get_db()) as db, db:
            cursor = db.execute(
                """
                INSERT INTO requests (
                    user_id, destination, departure_date, return_date, objective,
                    estimated_amount, daily_group, daily_range, has_overnight,
                    departure_time, return_time, distance_km, daily_factor, base_amount,
                    overnight_count, daily_quantity, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'enviada', ?, ?)
                """,
                (
                    user["id"],
                    request.form["destination"],
                    calculated["departure_date"],
                    calculated["return_date"],
                    request.form["objective"],
                    calculated["estimated_amount"],
                    calculated["daily_group"],
                    calculated["daily_range"],
                    1 if calculated["has_overnight"] else 0,
                    calculated["departure_time"],
                    calculated["return_time"],
                    calculated["distance_km"],
                    calculated["daily_factor"],
                    calculated["base_amount"],
                    calculated["overnight_count"],
                    calculated["daily_quantity"],
                    now,
                    now,
                ),
            )
            request_id = cursor.lastrowid

        for file_storage in request.files.getlist("attachments"):
            save_attachment(file_storage, request_id, "solicitacao")

        flash("Solicitação enviada para validação.", "success")
        return redirect(url_for("request_detail", request_id=request_id))

    return render_template("request_form.html", **request_form_context(user))


@app.route("/solicitacoes/<int:request_id>/editar", methods=["GET", "POST"])
@role_required("solicitante")
def edit_request(request_id):
    user = current_user()
    daily_request = get_request_or_404(request_id)
    if daily_request["user_id"] != user["id"]:
        abort(403)
    if daily_request["status"] != "correcao_solicitada":
        flash("Apenas solicitações com correção solicitada podem ser editadas.", "warning")
        return redirect(url_for("request_detail", request_id=request_id))

    if request.method == "POST":
        try:
            calculated = calculate_request_amount(user, request.form)
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("request_form.html", **request_form_context(user, daily_request))

        with closing(get_db()) as db, db:
            db.execute(
                """
                UPDATE requests
                SET destination = ?, departure_date = ?, return_date = ?, objective = ?,
                    estimated_amount = ?, daily_group = ?, daily_range = ?, has_overnight = ?,
                    departure_time = ?, return_time = ?, distance_km = ?, daily_factor = ?, base_amount = ?,
                    overnight_count = ?, daily_quantity = ?, status = 'corrigida', updated_at = ?
                WHERE id = ?
                """,
                (
                    request.form["destination"],
                    calculated["departure_date"],
                    calculated["return_date"],
                    request.form["objective"],
                    calculated["estimated_amount"],
                    calculated["daily_group"],
                    calculated["daily_range"],
                    1 if calculated["has_overnight"] else 0,
                    calculated["departure_time"],
                    calculated["return_time"],
                    calculated["distance_km"],
                    calculated["daily_factor"],
                    calculated["base_amount"],
                    calculated["overnight_count"],
                    calculated["daily_quantity"],
                    datetime.now().isoformat(timespec="seconds"),
                    request_id,
                ),
            )

        for file_storage in request.files.getlist("attachments"):
            save_attachment(file_storage, request_id, "solicitacao")

        flash("Solicitação corrigida e reenviada para validação.", "success")
        return redirect(url_for("request_detail", request_id=request_id))

    return render_template("request_form.html", **request_form_context(user, daily_request))


@app.route("/solicitacoes/<int:request_id>")
@login_required
def request_detail(request_id):
    daily_request = get_request_or_404(request_id)
    if not user_can_view(daily_request):
        abort(403)

    attachments = get_attachments(request_id)

    return render_template(
        "request_detail.html",
        daily_request=daily_request,
        attachments=attachments,
        process_progress=get_process_progress(daily_request["status"]),
    )


@app.route("/solicitacoes/<int:request_id>/prestacao", methods=["GET", "POST"])
@role_required("solicitante")
def submit_accountability(request_id):
    daily_request = get_request_or_404(request_id)
    if daily_request["user_id"] != current_user()["id"]:
        abort(403)
    if daily_request["status"] not in ["aprovada", "prestacao_correcao_solicitada"]:
        flash("A prestação de contas não está disponível para o status atual.", "warning")
        return redirect(url_for("request_detail", request_id=request_id))

    attachments = get_attachments(request_id)
    if request.method == "GET":
        return render_template(
            "form_prestacao.html",
            **accountability_form_context(daily_request, attachments),
        )

    displacement_files = request.files.getlist("displacement_attachments")
    objective_files = request.files.getlist("objective_attachments")
    try:
        valid_displacement_files, valid_objective_files = validate_accountability_form(
            request.form,
            displacement_files,
            objective_files,
            attachments,
        )
    except ValueError as error:
        flash(str(error), "danger")
        return render_template(
            "form_prestacao.html",
            **accountability_form_context(daily_request, attachments),
        )

    status = "prestacao_enviada"
    if daily_request["status"] == "prestacao_correcao_solicitada":
        status = "prestacao_corrigida"

    with closing(get_db()) as db, db:
        db.execute(
            """
            UPDATE requests
            SET accountability_text = ?, accountability_departure_time = ?,
                accountability_arrival_time = ?, transport_mode = ?,
                departure_km = ?, arrival_km = ?, refund_amount = ?,
                status = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                request.form["accountability_text"],
                request.form["accountability_departure_time"],
                request.form["accountability_arrival_time"],
                request.form["transport_mode"],
                request.form.get("departure_km") or None,
                request.form.get("arrival_km") or None,
                float(request.form.get("refund_amount") or 0),
                status,
                datetime.now().isoformat(timespec="seconds"),
                request_id,
            ),
        )

    for file_storage in valid_displacement_files:
        save_attachment(
            file_storage,
            request_id,
            "prestacao",
            "deslocamento",
            ACCOUNTABILITY_ALLOWED_EXTENSIONS,
        )
    for file_storage in valid_objective_files:
        save_attachment(
            file_storage,
            request_id,
            "prestacao",
            "objetivo",
            ACCOUNTABILITY_ALLOWED_EXTENSIONS,
        )

    flash("Prestação de contas enviada.", "success")
    return redirect(url_for("request_detail", request_id=request_id))


@app.route("/validador")
@role_required("validador")
def validator_dashboard():
    status_filter = request.args.get("status", "")
    search = request.args.get("q", "").strip()
    filters = []
    params = []

    if status_filter:
        filters.append("r.status = ?")
        params.append(status_filter)
    if search:
        filters.append("(r.destination LIKE ? OR u.name LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    with closing(get_db()) as db, db:
        requests = db.execute(
            f"""
            SELECT r.*, u.name AS requester_name
            FROM requests r
            JOIN users u ON u.id = r.user_id
            {where_clause}
            ORDER BY r.updated_at DESC
            """,
            params,
        ).fetchall()
    return render_template(
        "validator_dashboard.html",
        requests=requests,
        selected_status=status_filter,
        search=search,
    )


@app.route("/validador/solicitacoes/<int:request_id>/avaliar", methods=["POST"])
@role_required("validador")
def evaluate_request(request_id):
    action = request.form["action"]
    comment = request.form.get("validator_comment", "").strip()
    daily_request = get_request_or_404(request_id)
    is_accountability_review = daily_request["status"] in ACCOUNTABILITY_REVIEW_STATUSES

    if is_accountability_review:
        status_map = {
            "approve": "prestacao_aprovada",
            "approve_with_reservations": "prestacao_aprovada_ressalvas",
            "request_correction": "prestacao_correcao_solicitada",
            "reject": "rejeitada",
        }
    else:
        status_map = {
            "approve": "aprovada",
            "request_correction": "correcao_solicitada",
            "reject": "rejeitada",
        }

    if action not in status_map:
        abort(400)

    with closing(get_db()) as db, db:
        db.execute(
            """
            UPDATE requests
            SET status = ?, validator_comment = ?, updated_at = ?
            WHERE id = ?
            """,
            (status_map[action], comment, datetime.now().isoformat(timespec="seconds"), request_id),
        )

    flash("Avaliação registrada.", "success")
    return redirect(url_for("request_detail", request_id=request_id))


@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(get_demo_upload_folder(), filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
