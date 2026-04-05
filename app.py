import streamlit as st
import pandas as pd
from google import genai

# Configuración básica de la página
st.set_page_config(page_title="Marketplace Repuestos", page_icon="⚙️", layout="wide", initial_sidebar_state="expanded")

# --- CONFIGURACIÓN DE LA API KEY (Fija para la demo) ---
API_KEY = "AIzaSyCeuJf9PjARY0hBfq4olf95xCOAhr-jiVE" # <--- ¡Pega tu llave de Google AI Studio aquí!

# --- INICIALIZACIÓN DE VARIABLES DE ESTADO ---
if "pagina_actual" not in st.session_state:
    st.session_state.pagina_actual = "inicio"
if "producto_seleccionado" not in st.session_state:
    st.session_state.producto_seleccionado = None
if "carrito" not in st.session_state:
    st.session_state.carrito = []

# --- CARGA DE DATOS ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("repuestos.csv", encoding="utf-8", sep=None, engine="python")
    except UnicodeDecodeError:
        df = pd.read_csv("repuestos.csv", encoding="latin-1", sep=None, engine="python")
    df.columns = df.columns.str.strip()
    df['Marca'] = df['Vehiculo_Compatible'].str.split().str[0]
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("No se encontró el archivo 'repuestos.csv'.")
    st.stop()

# --- FUNCIONES DE NAVEGACIÓN Y CARRITO ---
def ir_a_inicio():
    st.session_state.pagina_actual = "inicio"
    st.session_state.producto_seleccionado = None

def ver_detalle(sku):
    st.session_state.producto_seleccionado = sku
    st.session_state.pagina_actual = "detalle"

def ver_carrito():
    st.session_state.pagina_actual = "carrito"

def agregar_al_carrito(producto):
    st.session_state.carrito.append(producto)
    st.toast(f"✅ ¡{producto['Nombre']} agregado al carrito!", icon="🛒")

def eliminar_del_carrito(index):
    item = st.session_state.carrito.pop(index)
    st.toast(f"🗑️ {item['Nombre']} eliminado", icon="❌")

# --- BARRA LATERAL (Navegación e IA) ---
with st.sidebar:
    st.title("⚙️ Mi Cuenta")
    
    if st.button("🏠 Catálogo Principal", use_container_width=True):
        ir_a_inicio()
    if st.button(f"🛒 Mi Carrito ({len(st.session_state.carrito)})", use_container_width=True):
        ver_carrito()
        
    st.divider()
    
    # Asistente IA Integrado
    st.title("🤖 Tuercas - Asesor IA")
    
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = [{"rol": "assistant", "contenido": "¡Hola! Soy Tuercas 🤖. Dime qué carro tienes o qué repuesto buscas y te ayudo a comparar precios."}]

    for msg in st.session_state.mensajes:
        with st.chat_message(msg["rol"]):
            st.markdown(msg["contenido"])

    if prompt := st.chat_input("Ej. ¿Cuál es el filtro más barato para Lancer?"):
        st.session_state.mensajes.append({"rol": "user", "contenido": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if not API_KEY:
                st.error("⚠️ Falta configurar la API Key en el código.")
            else:
                try:
                    client = genai.Client(api_key=API_KEY)
                    
                    # SOLUCIÓN DE TILDES: Usar JSON con force_ascii=False para respetar el español
                    contexto_datos = df.to_json(orient="records", force_ascii=False)
                    
                    prompt_sistema = f"""
                    Eres 'Tuercas', el mecánico virtual estrella de un Marketplace de repuestos.
                    Habla como un experto automotriz, amable y directo.
                    Responde SOLO usando los datos de este inventario en formato JSON:
                    {contexto_datos}
                    
                    Reglas:

                    - Si te preguntan por opciones, compara precios y menciona el proveedor.
                    - Si no lo tenemos, dilo claramente.
                    - Respeta los acentos y el idioma español.
                    
                    Pregunta del cliente: {prompt}
                    """
                    respuesta = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt_sistema
                    )
                    st.markdown(respuesta.text)
                    st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta.text})
                except Exception as e:
                    st.error(f"Error en la IA: {e}")

# --- VISTA 1: INICIO (Catálogo) ---
if st.session_state.pagina_actual == "inicio":
    st.title("🏁 Marketplace: Repuestos Automotrices")
    st.write("Cotiza, compara y compra repuestos OEM y alternativos en segundos.")
    
    busqueda = st.text_input("🔍 Buscar por SKU, Nombre o Vehículo...", "")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        marcas_disponibles = ["Todas"] + list(df['Marca'].unique())
        marca_seleccionada = st.selectbox("Filtrar por Marca", marcas_disponibles)
    with col_f2:
        categorias_disponibles = ["Todas"] + list(df['Categoria'].unique())
        categoria_seleccionada = st.selectbox("Filtrar por Categoría", categorias_disponibles)

    df_filtrado = df.copy()
    if busqueda:
        mask = df_filtrado.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df_filtrado = df_filtrado[mask]
    if marca_seleccionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Marca'] == marca_seleccionada]
    if categoria_seleccionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Categoria'] == categoria_seleccionada]

    st.divider()

    if busqueda == "" and marca_seleccionada == "Todas" and categoria_seleccionada == "Todas":
        st.subheader("🔥 Ofertas y Destacados")
        df_a_mostrar = df_filtrado.head(3)
    else:
        st.subheader(f"Resultados encontrados ({len(df_filtrado)})")
        df_a_mostrar = df_filtrado

    cols = st.columns(3)
    for index, row in df_a_mostrar.reset_index().iterrows():
        col = cols[index % 3]
        with col.container(border=True):
            st.image(row["URL_Imagen"], use_container_width=True)
            st.subheader(row["Nombre"])
            st.metric(label="Precio", value=f"${row['Precio']:.2f}")
            st.caption(f"Vehículo: {row['Vehiculo_Compatible']}")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                st.button("📄 Detalles", key=f"det_{row['SKU']}", on_click=ver_detalle, args=(row['SKU'],), use_container_width=True)
            with col_btn2:
                st.button("🛒 Agregar", key=f"add_{row['SKU']}", type="primary", on_click=agregar_al_carrito, args=(row.to_dict(),), use_container_width=True)

    st.markdown("""
    <br><br>
    <div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px; color: #555;'>
        <h4>🤝 Distribuidores Autorizados</h4>
        <p style='font-size: 18px;'><b>TOYOTA &nbsp;|&nbsp; NISSAN &nbsp;|&nbsp; MITSUBISHI &nbsp;|&nbsp; SUPER REPUESTOS</b></p>
        <p style='font-size: 12px; margin-top: 10px;'>© 2026 Marketplace B2B2C. ESEN - Innovación e IA.</p>
    </div>
    """, unsafe_allow_html=True)

# --- VISTA 2: DETALLE DEL PRODUCTO ---
elif st.session_state.pagina_actual == "detalle":
    producto = df[df['SKU'] == st.session_state.producto_seleccionado].iloc[0]
    st.button("⬅️ Volver al catálogo", on_click=ir_a_inicio)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(producto["URL_Imagen"], use_container_width=True)
        if producto["Validacion_OEM"] == "Sí":
            st.success("✅ Validación OEM Confirmada")
        else:
            st.warning("⚠️ Repuesto Alternativo")

    with col2:
        st.title(producto["Nombre"])
        st.header(f"${producto['Precio']:.2f}")
        
        st.markdown("### Especificaciones Técnicas")
        datos_tabla = {
            "Característica": ["SKU", "Marca Vehículo", "Modelo", "Proveedor", "Stock Disponible", "Tiempo de Entrega"],
            "Detalle": [producto['SKU'], producto['Marca'], producto['Vehiculo_Compatible'], producto['Proveedor'], producto['Stock'], producto['Entrega']]
        }
        st.table(pd.DataFrame(datos_tabla))
        st.button("🛒 Agregar al Carrito", type="primary", on_click=agregar_al_carrito, args=(producto.to_dict(),), use_container_width=True)

# --- VISTA 3: CARRITO DE COMPRAS ---
elif st.session_state.pagina_actual == "carrito":
    st.title("🛒 Mi Carrito de Compras")
    st.button("⬅️ Seguir comprando", on_click=ir_a_inicio)
    
    if not st.session_state.carrito:
        st.info("Tu carrito está vacío. ¡Ve al catálogo para agregar repuestos!")
    else:
        total = 0
        for i, item in enumerate(st.session_state.carrito):
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
                with col1:
                    st.image(item["URL_Imagen"], width=80)
                with col2:
                    st.subheader(item["Nombre"])
                    st.caption(f"SKU: {item['SKU']} | Proveedor: {item['Proveedor']}")
                with col3:
                    st.subheader(f"${item['Precio']:.2f}")
                    total += float(item['Precio'])
                with col4:
                    st.button("🗑️ Quitar", key=f"del_{i}", on_click=eliminar_del_carrito, args=(i,), use_container_width=True)
        
        st.divider()
        col_vacia, col_total = st.columns([3, 1])
        with col_total:
            st.metric("Total a Pagar", f"${total:.2f}")
            if st.button("Proceder al Pago", type="primary", use_container_width=True):
                st.balloons()
                st.success("¡Simulación de pago exitosa! Tu pedido está siendo procesado.")
                st.session_state.carrito = [] # Vacía el carrito