import streamlit as st
from dotenv import load_dotenv
import requests
import json
import re
from typing import Optional
load_dotenv()

# --- AUTENTICACIÓN POR CONTRASEÑA ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Contraseña", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Contraseña", type="password", on_change=password_entered, key="password")
        st.error("Contraseña incorrecta")
        return False
    else:
        return True

if not check_password():
    st.stop()

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

# Configuración de la página
st.set_page_config(
    page_title="AgentPRO Chat",
    page_icon="🤖",
    layout="wide"
)

# Título y descripción
st.title("🤖 AgentPRO - Chat con IA para tu showroom de lujo")
st.markdown("---")

# Inicializar el modelo en session_state si no existe
if "llm" not in st.session_state:
    st.session_state.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

# Inicializar historial de chat si no existe
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar para configuraciones
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Selector de modelo
    model = st.selectbox(
        "Modelo de IA",
        ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        index=0
    )
    
    # Control de temperatura
    temperature = st.slider(
        "Creatividad (Temperature)",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="Valores más altos = más creativo, valores más bajos = más determinista"
    )
    
    # Botón para limpiar chat
    if st.button("🗑️ Limpiar Chat", type="secondary"):
        st.session_state.messages = []
        st.rerun()
    
    # Información del modelo
    st.markdown("---")
    st.markdown("### 📊 Información")
    st.markdown(f"**Modelo:** {model}")
    st.markdown(f"**Temperatura:** {temperature}")
    st.markdown(f"**Mensajes:** {len(st.session_state.messages)}")

# Actualizar modelo si cambió la configuración
if (st.session_state.llm.model_name != model or 
    st.session_state.llm.temperature != temperature):
    st.session_state.llm = ChatOpenAI(model=model, temperature=temperature)

# --- FUNCIONES AUXILIARES ---

API_BASE = "https://dsquaredbsas.replit.app/api/ai"

# Detectar si la pregunta es de seguimiento
SEGUIMIENTO_KEYWORDS = [
    "de estas", "de los que me mostraste", "de los anteriores", "la blanca", "la negra", "la primera", "la segunda", "la tercera", "la de color", "la que es"
]

def es_pregunta_seguimiento(pregunta):
    pregunta_lower = pregunta.lower()
    return any(kw in pregunta_lower for kw in SEGUIMIENTO_KEYWORDS)

# Filtrar productos por color y/o tipo y/o marca y/o talle
def filtrar_productos(productos, atributos):
    filtrados = productos
    if atributos.get("color"):
        filtrados = [p for p in filtrados if atributos["color"].lower() in p["color"].lower()]
    if atributos.get("type"):
        filtrados = [p for p in filtrados if atributos["type"].lower() in p["name"].lower() or atributos["type"].lower() in p["category"].lower()]
    if atributos.get("brand"):
        filtrados = [p for p in filtrados if atributos["brand"].lower() in p["brand"].lower()]
    return filtrados

# --- NUEVO: Desambiguar producto usando el LLM ---
def desambiguar_producto_llm(productos, pregunta, llm):
    if not productos:
        return []
    # Construir listado para el prompt
    listado = "\n".join([
        f"{i+1}. Nombre: {p['name']}, Marca: {p['brand']}, Color: {p['color']}, Talles: {[s['value'] for s in p['sizes'] if s['available']]}"
        for i, p in enumerate(productos)
    ])
    prompt = (
        f"Dado el siguiente listado de productos ofrecidos:\n{listado}\n"
        f"Y la pregunta del usuario: '{pregunta}'\n"
        "Si la pregunta hace referencia explícita a uno o más productos del listado (por ejemplo, usando color, orden, o diciendo 'de estos', 'la segunda', etc.), responde SOLO con una lista de índices (por ejemplo: [1] o [2,3]) de los productos a los que se refiere el usuario. "
        "Si la pregunta es una nueva consulta sobre otra marca, tipo, o no hace referencia a productos previos, responde [].\n"
        "Ejemplos:\n"
        "Listado:\n"
        "1. Nombre: Remera Balenciaga, Marca: Balenciaga, Color: Negro\n"
        "2. Nombre: Remera Off-White, Marca: Off-White, Color: Blanco\n"
        "Pregunta: '¿La blanca en qué talles está?'\n"
        "Respuesta: [2]\n"
        "Pregunta: '¿Y la negra?'\n"
        "Respuesta: [1]\n"
        "Pregunta: '¿Qué remeras de Gucci tenés?'\n"
        "Respuesta: []\n"
        "Pregunta: '¿De estos, la segunda?'\n"
        "Respuesta: [2]\n"
        "Pregunta: '¿Y de Off-White qué tenés?'\n"
        "Respuesta: []\n"
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    # Intentar extraer la lista de índices del LLM
    try:
        match = re.search(r'\[(.*?)\]', response.content)
        if match:
            indices = [int(i.strip()) for i in match.group(1).split(',') if i.strip().isdigit()]
            return indices
        else:
            return []
    except Exception:
        return []

# 1. Extraer atributos relevantes de la consulta usando el LLM
def extraer_atributos_llm(pregunta, llm):
    prompt = (
        "Eres un extractor de atributos para un sistema de stock de prendas de lujo. "
        "Dada una consulta de usuario, responde SOLO con un JSON válido y nada más. "
        "El JSON debe tener las claves: brand, type, color, size. Si algún dato no está, déjalo vacío. "
        "Ejemplos:\n"
        "'¿Hay remeras Gucci verde en talle M?' => {\"brand\":\"Gucci\",\"type\":\"remera\",\"color\":\"verde\",\"size\":\"M\"}\n"
        "'¿Tienen pantalones Louis Vuitton negros?' => {\"brand\":\"Louis Vuitton\",\"type\":\"pantalón\",\"color\":\"negro\",\"size\":\"\"}\n"
        "'¿Hay camperas Moncler?' => {\"brand\":\"Moncler\",\"type\":\"campera\",\"color\":\"\",\"size\":\"\"}\n"
        "'¿Remeras talle S?' => {\"brand\":\"\",\"type\":\"remera\",\"color\":\"\",\"size\":\"S\"}\n"
        "'¿Hay algo de Dior?' => {\"brand\":\"Dior\",\"type\":\"\",\"color\":\"\",\"size\":\"\"}\n"
        f"Consulta: '{pregunta}'"
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    # Intentar extraer el primer bloque JSON de la respuesta
    try:
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return data
        else:
            return {"brand": "", "type": "", "color": "", "size": ""}
    except Exception as e:
        return {"brand": "", "type": "", "color": "", "size": ""}

# 2. Consultar la API de stock
def consultar_stock_api(brand, type, color, size):
    url = f"{API_BASE}/products/search"
    params = {}
    if brand: params['brand'] = brand
    if type: params['type'] = type
    if color: params['color'] = color
    if size: params['size'] = size
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            return None
    except Exception:
        return None

# 3. Generar respuesta natural con el LLM y mostrar imágenes
def mostrar_productos_en_chat(matches: list, st_container: Optional[any] = None, tipo_consulta="exploracion"):
    if not matches:
        return
    if st_container is None:
        st_container = st
    st_container.markdown("**Productos encontrados:**")
    for producto in matches[:3]:  # Limitar a 3 productos para no saturar
        cols = st_container.columns([1, 3])
        with cols[0]:
            st.image(producto["imageUrl"], width=100)
        with cols[1]:
            talles = ', '.join([s['value'] for s in producto['sizes'] if s['available']])
            st.markdown(f"**{producto['name']}**  ")
            st.markdown(f"Marca: {producto['brand']}")
            st.markdown(f"Color: {producto['color']}")
            st.markdown(f"Talles disponibles: {talles if talles else 'Ninguno'}")
            st.markdown(f"Precio: ${producto['price']}")
    # Solo mostrar la pregunta de selección si es consulta de selección
    if tipo_consulta == "seleccion" and len(matches) > 1:
        st_container.info("¿Te refieres a alguno de estos modelos?")

def respuesta_natural_llm(pregunta, atributos, resultado_api, llm, st_container=None, tipo_consulta="exploracion"):
    if not resultado_api or resultado_api.get("totalFound", 0) == 0:
        return "No se encontró ese producto en el stock. ¿Quieres que busque algo similar?"
    matches = resultado_api["matches"]
    if st_container:
        mostrar_productos_en_chat(matches, st_container, tipo_consulta)
    producto = matches[0]
    # Si la consulta es de stock específico (talle)
    if tipo_consulta == "stock" and atributos.get("size"):
        if producto.get("requestedSize") and producto["requestedSize"] and producto["requestedSize"].get("available"):
            stock = producto["requestedSize"]["stock"]
            nombre = producto["name"]
            marca = producto["brand"]
            color = producto["color"]
            talle = producto["requestedSize"]["value"]
            return f"Sí, hay stock de {nombre} {marca} {color} en talle {talle}. Quedan {stock} unidades."
        else:
            # Buscar talles disponibles
            talles_disp = [s['value'] for s in producto['sizes'] if s['available']]
            if talles_disp:
                return f"No hay stock en ese talle, pero sí en los talles: {', '.join(talles_disp)}."
            else:
                return "No hay stock disponible para ese producto."
    # Si la consulta es de selección/seguimiento
    elif tipo_consulta == "seleccion":
        return "Aquí tienes la información del producto que seleccionaste. Si quieres saber más, dime el talle o color que te interesa."
    # Si la consulta es de exploración
    else:
        return "Estos son los modelos que tenemos disponibles:" if len(matches) > 1 else "Este es el modelo que tenemos disponible:"

# --- FLUJO DEL CHAT ---

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Escribe tu mensaje aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant") as assistant_container:
        message_placeholder = st.empty()
        try:
            # 1. Extraer atributos
            atributos = extraer_atributos_llm(prompt, st.session_state.llm)
            tipo_consulta = "exploracion"
            productos_contexto = None
            confirmacion_pendiente = False
            # --- Lógica previa: comparar atributos con productos previos ---
            es_nueva_consulta = False
            if hasattr(st.session_state, 'last_products') and st.session_state.last_products:
                # Si la marca o el tipo cambian respecto a los productos previos, es nueva consulta
                marcas_previas = set(p['brand'].lower() for p in st.session_state.last_products if p.get('brand'))
                tipos_previos = set(p['name'].lower() for p in st.session_state.last_products if p.get('name'))
                marca_actual = atributos.get('brand', '').lower()
                tipo_actual = atributos.get('type', '').lower()
                if (marca_actual and marca_actual not in marcas_previas) or (tipo_actual and all(tipo_actual not in n for n in tipos_previos)):
                    es_nueva_consulta = True
            # Si es nueva consulta, no intentar desambiguar
            if hasattr(st.session_state, 'last_products') and st.session_state.last_products and not es_nueva_consulta:
                indices = desambiguar_producto_llm(st.session_state.last_products, prompt, st.session_state.llm)
                if indices:
                    productos_contexto = [st.session_state.last_products[i-1] for i in indices if 0 < i <= len(st.session_state.last_products)]
                    resultado = {"matches": productos_contexto, "totalFound": len(productos_contexto)}
                    tipo_consulta = "seleccion"
                else:
                    if len(st.session_state.last_products) > 0:
                        productos_contexto = [st.session_state.last_products[-1]]
                        resultado = {"matches": productos_contexto, "totalFound": 1}
                        confirmacion_pendiente = True
                        tipo_consulta = "seleccion"
                    else:
                        resultado = None
            else:
                resultado = None
            # Si no hay contexto o no se pudo desambiguar, consulta normal a la API
            if not productos_contexto:
                resultado = consultar_stock_api(
                    atributos.get("brand"),
                    atributos.get("type"),
                    atributos.get("color"),
                    atributos.get("size")
                )
                if resultado and resultado.get("matches"):
                    st.session_state.last_products = resultado["matches"]
                else:
                    st.session_state.last_products = []
                if atributos.get("size"):
                    tipo_consulta = "stock"
            if resultado and resultado.get("matches"):
                mostrar_productos_en_chat(resultado["matches"], assistant_container, tipo_consulta)
            respuesta = respuesta_natural_llm(prompt, atributos, resultado, st.session_state.llm, tipo_consulta=tipo_consulta)
            if confirmacion_pendiente:
                respuesta = ("No entendí a qué producto te refieres exactamente, así que te muestro información del último producto ofrecido. "
                             "¿Te refieres a este? Si no, por favor aclara a cuál te refieres.") + "\n\n" + respuesta
            message_placeholder.markdown(respuesta)
            st.session_state.messages.append({"role": "assistant", "content": respuesta})
        except Exception as e:
            error_message = f"❌ Error: {str(e)}"
            message_placeholder.markdown(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Desarrollado con ❤️ usando LangChain, OpenAI y tu API de stock</p>
    </div>
    """,
    unsafe_allow_html=True
) 