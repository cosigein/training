import warnings
# Silenciar advertencias de Eventlet y Limiter para un arranque limpio
warnings.filterwarnings("ignore", message="Eventlet is deprecated")
warnings.filterwarnings("ignore", category=UserWarning, module="flask_limiter")

from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000)
