# AgentPRO - Chat con IA 🤖

Este proyecto te permite interactuar con modelos de IA de OpenAI usando LangChain a través de diferentes interfaces.

## 🚀 Opciones de Chat

### 1. Chat por Terminal (chat.py)
Una interfaz simple de línea de comandos para conversar con la IA.

**Para usar:**
```bash
python3 chat.py
```

**Características:**
- ✅ Conversación interactiva en terminal
- ✅ Historial de chat mantenido durante la sesión
- ✅ Comandos especiales: `salir`, `limpiar`
- ✅ Manejo de errores
- ✅ Fácil de usar

### 2. Chat Web con Streamlit (web_chat.py)
Una interfaz web moderna y visual para una mejor experiencia de usuario.

**Para usar:**
```bash
streamlit run web_chat.py
```

**Características:**
- 🌐 Interfaz web moderna
- ⚙️ Configuración en tiempo real del modelo y temperatura
- 📊 Información del chat en tiempo real
- 🎨 Interfaz visual atractiva
- 📱 Responsive design
- 🔄 Historial persistente durante la sesión

## 📋 Requisitos

Asegúrate de tener instaladas las dependencias:

```bash
pip3 install python-dotenv langchain-openai streamlit
```

## 🔧 Configuración

1. Crea un archivo `.env` en la raíz del proyecto
2. Agrega tu API key de OpenAI:

```env
OPENAI_API_KEY=tu_api_key_aqui
```

## 🎯 Uso

### Chat por Terminal
```bash
python3 chat.py
```

Comandos disponibles:
- `salir` - Terminar la conversación
- `limpiar` - Borrar el historial de chat

### Chat Web
```bash
streamlit run web_chat.py
```

Luego abre tu navegador en `http://localhost:8501`

## 🔧 Configuración Avanzada

### Modelos Disponibles
- `gpt-4o` - Modelo más avanzado (recomendado)
- `gpt-4o-mini` - Versión más rápida y económica
- `gpt-3.5-turbo` - Modelo balanceado

### Parámetros
- **Temperature**: Controla la creatividad (0.0 = determinista, 2.0 = muy creativo)
- **Model**: Selecciona el modelo de IA a usar

## 📁 Estructura del Proyecto

```
AgentPRO/
├── main.py          # Script básico de ejemplo
├── chat.py          # Chat por terminal
├── web_chat.py      # Chat web con Streamlit
├── .env             # Variables de entorno (crear)
└── README.md        # Este archivo
```

## 🛠️ Desarrollo

Para agregar nuevas funcionalidades:

1. **Nuevos comandos**: Modifica `chat.py` para agregar comandos especiales
2. **Nuevas características**: Extiende `web_chat.py` con widgets de Streamlit
3. **Integración con APIs**: Usa LangChain para conectar con otros servicios

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Puedes:
- Reportar bugs
- Sugerir nuevas características
- Mejorar la documentación
- Agregar nuevos modelos de IA

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT. 