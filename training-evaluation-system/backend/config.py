import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(BASE_DIR, "data.db")
)

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
MAX_UPLOAD_SIZE = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg",
    ".gif", ".bmp", ".txt", ".xlsx", ".xls", ".ppt", ".pptx", ".csv",
    # 源代码类扩展名
    ".py", ".js", ".java", ".cpp", ".c", ".h", ".html", ".css", ".vue",
    ".jsx", ".ts", ".tsx", ".json", ".xml", ".sql", ".php", ".go", ".rb",
    ".rs", ".cs", ".swift", ".kt", ".m", ".mm", ".sh", ".bat", ".ps1",
    ".yaml", ".yml", ".toml", ".ini", ".properties", ".md", ".svg", ".webp"
}

# ==================== 大模型配置（对话/生成） ====================
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")          # 接口兼容 OpenAI
LLM_API_PASSWORD = os.environ.get("LLM_API_PASSWORD", "")        # APIPassword（优先使用，Bearer认证）
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")                  # API Key（签名认证）
LLM_API_SECRET = os.environ.get("LLM_API_SECRET", "")            # API Secret（签名认证）
LLM_APP_ID = os.environ.get("LLM_APP_ID", "")                    # AppID（签名认证）
LLM_API_BASE = os.environ.get("LLM_API_BASE", "https://spark-api-open.xf-yun.com/v1")  # 基础地址
LLM_MODEL = os.environ.get("LLM_MODEL", "4.0Ultra")              # 官方模型名：4.0Ultra, generalv3.5, generalv3, lite
# ===================================================================================

# ==================== Embedding 配置（RAG 向量检索） ====================
# 可独立配置，例如使用 SiliconFlow、OpenAI、Ollama 等 embedding 服务
EMBEDDING_PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "openai")  # openai / ollama
EMBEDDING_API_BASE = os.environ.get("EMBEDDING_API_BASE", "https://api.siliconflow.cn/v1")
EMBEDDING_API_KEY = os.environ.get("EMBEDDING_API_KEY", "")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")
# ===================================================================================

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")

REPORT_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

# 作业上传目录（文件存磁盘，不入库）
UPLOAD_HOMEWORK_DIR = os.path.join(BASE_DIR, '..', 'upload', 'homework')
os.makedirs(UPLOAD_HOMEWORK_DIR, exist_ok=True)

# 作业允许的文件格式
ALLOWED_HOMEWORK_EXTENSIONS = {'.pdf', '.doc', '.docx', '.mp4'}

# 作业单文件大小限制（默认100MB）
MAX_HOMEWORK_SIZE = 100 * 1024 * 1024

# MySQL 配置（用户信息库：teachers / admins 表）—— 请根据实际情况修改
MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "123456")   # 请修改为你的数据库密码
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "信息")      # 数据库名称