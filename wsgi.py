import os
import warnings
# Silenciar advertencias de Eventlet y Limiter para un arranque limpio
warnings.filterwarnings("ignore", message="Eventlet is deprecated")
warnings.filterwarnings("ignore", category=UserWarning, module="flask_limiter")

from app import create_app, socketio

_cfg = os.environ.get("FLASK_CONFIG") or (
    "production" if os.environ.get("FLASK_ENV") == "production" else "development"
)
app = create_app(_cfg)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=4000)
