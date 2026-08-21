/* ─────────────────────────────────────────────────────────────
   AmmaIA — Frontend Logic (Chat RAG, Auth, Admin, Attachments & PDF)
───────────────────────────────────────────────────────────── */

function resolveApiBase() {
  const custom = localStorage.getItem("ammaia_custom_backend");
  if (custom) return custom.replace(/\/$/, "");

  // Si se abre el archivo localmente como file:///
  if (window.location.protocol === "file:") {
    return "http://127.0.0.1:8000";
  }

  // Si se aloja en GitHub Pages (ej: ldpcicnm2012.github.io)
  if (window.location.hostname.includes("github.io")) {
    const renderUrl = localStorage.getItem("ammaia_render_url");
    return renderUrl || "https://ammaia-backend.onrender.com";
  }

  return window.location.origin;
}

let API_BASE = resolveApiBase();

let currentUser = null;
let currentToken = localStorage.getItem("ammaia_token") || localStorage.getItem("ammayia_token") || "";
let currentChatId = null;
let currentMessages = [];
let isAuthModeLogin = true;
let currentAttachment = null; // { name, text, size }

// ── Inicialización ──
document.addEventListener("DOMContentLoaded", async () => {
  initEventListeners();
  if (currentToken) {
    await verifySession();
  } else {
    updateUserDisplay(null);
  }
});

// ── Configuración de Eventos ──
function initEventListeners() {
  const chatInput = document.getElementById("chat-input");
  const btnSend = document.getElementById("btn-send");
  const btnNewChat = document.getElementById("btn-new-chat");
  const btnAuthToggle = document.getElementById("btn-auth-toggle");
  const btnExportWord = document.getElementById("btn-export-word");
  const btnExportPdf = document.getElementById("btn-export-pdf");
  const btnOpenAdmin = document.getElementById("btn-open-admin-modal");
  const btnOpenBoe = document.getElementById("btn-open-boe-modal");

  // Adjuntar archivos
  const btnAttach = document.getElementById("btn-attach-file");
  const fileInput = document.getElementById("file-attachment-input");
  const btnRemoveAttach = document.getElementById("btn-remove-attachment");

  if (btnAttach && fileInput) {
    btnAttach.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", handleFileSelected);
  }

  if (btnRemoveAttach) {
    btnRemoveAttach.addEventListener("click", removeCurrentAttachment);
  }

  // Drag and drop en el chat
  const viewport = document.getElementById("chat-viewport");
  viewport.addEventListener("dragover", (e) => {
    e.preventDefault();
    viewport.classList.add("drag-over");
  });
  viewport.addEventListener("dragleave", () => {
    viewport.classList.remove("drag-over");
  });
  viewport.addEventListener("drop", (e) => {
    e.preventDefault();
    viewport.classList.remove("drag-over");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  });

  // Auto-resize y envío con Enter
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      enviarConsulta();
    }
  });

  chatInput.addEventListener("input", () => {
    chatInput.style.height = "auto";
    chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + "px";
  });

  btnSend.addEventListener("click", enviarConsulta);
  btnNewChat.addEventListener("click", nuevoChat);
  btnExportWord.addEventListener("click", () => exportarDictamenWord());
  if (btnExportPdf) {
    btnExportPdf.addEventListener("click", () => exportarDictamenPDF());
  }

  // Chips de preguntas rápidas
  document.querySelectorAll(".prompt-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const q = chip.getAttribute("data-query");
      if (q) {
        chatInput.value = q;
        enviarConsulta();
      }
    });
  });

  // Modales
  btnAuthToggle.addEventListener("click", () => {
    if (currentUser) {
      cerrarSesion();
    } else {
      abrirModalAuth();
    }
  });

  document.getElementById("btn-close-auth").addEventListener("click", () => cerrarModal("modal-auth"));
  document.getElementById("tab-login").addEventListener("click", () => setAuthTab(true));
  document.getElementById("tab-register").addEventListener("click", () => setAuthTab(false));
  document.getElementById("auth-form").addEventListener("submit", handleAuthSubmit);

  // Admin Modal
  btnOpenAdmin.addEventListener("click", abrirModalAdmin);
  document.getElementById("btn-close-admin").addEventListener("click", () => cerrarModal("modal-admin"));

  // BOE Modal
  btnOpenBoe.addEventListener("click", abrirModalBoe);
  document.getElementById("btn-close-boe").addEventListener("click", () => cerrarModal("modal-boe"));
}

// ── Gestión de Archivos Adjuntos (PDF, DOCX, TXT) ──
async function handleFileSelected(e) {
  if (e.target.files && e.target.files.length > 0) {
    await processFile(e.target.files[0]);
    e.target.value = "";
  }
}

async function processFile(file) {
  if (!currentUser) {
    abrirModalAuth();
    return;
  }

  const preview = document.getElementById("attachment-preview-container");
  const nameEl = document.getElementById("attachment-name");
  const sizeEl = document.getElementById("attachment-size");
  const iconEl = document.getElementById("attachment-icon");

  nameEl.textContent = `Extrayendo texto de ${file.name}...`;
  sizeEl.textContent = "";
  preview.style.display = "flex";

  const ext = file.name.split(".").pop().toLowerCase();
  iconEl.textContent = ext === "pdf" ? "📕" : (ext.includes("doc") ? "📄" : "📑");

  const formData = new FormData();
  formData.append("archivo", file);

  try {
    const res = await fetch(`${API_BASE}/chat/subir-archivo`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${currentToken}` },
      body: formData
    });

    const data = await res.json();
    if (res.ok && data.success) {
      currentAttachment = {
        name: data.nombre_archivo,
        text: data.texto,
        size: formatBytes(file.size)
      };
      nameEl.textContent = currentAttachment.name;
      sizeEl.textContent = `(${currentAttachment.size})`;
    } else {
      alert("No se pudo extraer el texto del archivo: " + (data.detail || "Error desconocido"));
      removeCurrentAttachment();
    }
  } catch (err) {
    alert("Error de conexión al subir el archivo.");
    removeCurrentAttachment();
  }
}

function removeCurrentAttachment() {
  currentAttachment = null;
  const preview = document.getElementById("attachment-preview-container");
  if (preview) preview.style.display = "none";
}

function formatBytes(bytes) {
  if (!bytes) return "0 KB";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

// ── Gestión de Sesiones y Usuario ──
async function verifySession() {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    if (res.ok) {
      const data = await res.json();
      currentUser = data.usuario;
      updateUserDisplay(data);
      cargarHistorial();
    } else {
      cerrarSesion(false);
    }
  } catch (err) {
    console.error("Error verificando sesión:", err);
  }
}

function updateUserDisplay(data) {
  const nameEl = document.getElementById("display-user-name");
  const roleEl = document.getElementById("display-user-role");
  const quotaBadge = document.getElementById("display-quota-badge");
  const quotaText = document.getElementById("quota-text");
  const authBtnText = document.getElementById("auth-btn-text");
  const btnAdmin = document.getElementById("btn-open-admin-modal");

  if (!currentUser) {
    nameEl.textContent = "Invitado";
    roleEl.textContent = "Sin registrar";
    quotaBadge.className = "quota-pill";
    quotaText.textContent = "Inicia sesión para consultar";
    authBtnText.textContent = "Iniciar Sesión";
    btnAdmin.style.display = "none";
    const delBtn = document.getElementById("btn-delete-account");
    if (delBtn) delBtn.style.display = "none";
    return;
  }

  nameEl.textContent = currentUser.nombre || currentUser.email;
  roleEl.textContent = currentUser.rol || "Abogado";
  authBtnText.textContent = "Cerrar Sesión";
  const delBtn = document.getElementById("btn-delete-account");
  if (delBtn) delBtn.style.display = "flex";

  // Mostrar botón admin si corresponde
  if (currentUser.is_admin) {
    btnAdmin.style.display = "flex";
  } else {
    btnAdmin.style.display = "none";
  }

  // Actualizar Cuota
  if (data && data.cuota) {
    const q = data.cuota;
    if (q.is_premium) {
      quotaBadge.className = "quota-pill premium";
      quotaText.textContent = "👑 Premium Ilimitado";
    } else {
      quotaBadge.className = "quota-pill";
      quotaText.textContent = `${q.usados_hoy}/${q.limite_diario} consultas hoy`;
    }
  }
}

function cerrarSesion(alerta = true) {
  currentUser = null;
  currentToken = "";
  localStorage.removeItem("ammaia_token");
  localStorage.removeItem("ammayia_token");
  updateUserDisplay(null);
  nuevoChat();
  if (alerta) alert("Has cerrado sesión en AmmaIA.");
}

async function solicitarEliminarCuenta() {
  if (!currentUser) return;
  const confirmacion = confirm(`⚠️ ATENCIÓN: ¿Estás seguro de que deseas eliminar definitivamente tu cuenta (${currentUser.email}) y todos tus dictámenes legales del servidor?\n\nEsta acción es irreversible conforme al Derecho al Olvido (Art. 17 RGPD).`);
  if (!confirmacion) return;

  try {
    const res = await fetch(`${API_BASE}/auth/eliminar-mi-cuenta`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    const data = await res.json();
    if (res.ok) {
      alert(data.mensaje || "Tu cuenta ha sido eliminada con éxito.");
      cerrarSesion(false);
    } else {
      alert(data.detail || "Error al eliminar la cuenta.");
    }
  } catch (err) {
    alert("Error de conexión al solicitar el borrado de la cuenta.");
  }
}

// ── Auth Modal Logic ──
function abrirModalAuth() {
  setAuthTab(true);
  document.getElementById("modal-auth").classList.add("active");
}

function cerrarModal(id) {
  document.getElementById(id).classList.remove("active");
}

function setAuthTab(isLogin) {
  isAuthModeLogin = isLogin;
  document.getElementById("tab-login").style.borderColor = isLogin ? "var(--gold-primary)" : "transparent";
  document.getElementById("tab-register").style.borderColor = !isLogin ? "var(--gold-primary)" : "transparent";
  document.getElementById("group-nombre").style.display = isLogin ? "none" : "flex";
  document.getElementById("group-rol").style.display = isLogin ? "none" : "flex";
  document.getElementById("btn-auth-submit").textContent = isLogin ? "Entrar" : "Crear Cuenta de Letrado";
  document.getElementById("auth-error-msg").textContent = "";
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const email = document.getElementById("auth-email").value.trim();
  const password = document.getElementById("auth-password").value;
  const nombre = document.getElementById("auth-nombre").value.trim();
  const rol = document.getElementById("auth-rol").value;
  const errEl = document.getElementById("auth-error-msg");

  errEl.textContent = "Conectando...";
  const url = isAuthModeLogin ? `${API_BASE}/auth/login` : `${API_BASE}/auth/registro`;
  const body = isAuthModeLogin ? { email, password } : { email, password, nombre, rol };

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (!res.ok) {
      errEl.textContent = data.detail || "Error en la autenticación.";
      return;
    }

    currentToken = data.token;
    localStorage.setItem("ammaia_token", currentToken);
    currentUser = data.usuario;
    updateUserDisplay(data);
    cerrarModal("modal-auth");
    cargarHistorial();
  } catch (err) {
    console.error("Error en fetch de autenticación:", err);
    if (window.location.protocol === "file:") {
      errEl.innerHTML = `⚠️ No se pudo conectar con el servidor local (<b>http://127.0.0.1:8000</b>).<br>Asegúrate de ejecutar <code>python run_backend.py</code> en tu terminal.`;
    } else {
      errEl.innerHTML = `⚠️ No se pudo conectar con el servidor (<code>${API_BASE}</code>).<br>Verifica tu conexión y que el backend esté activo.`;
    }
  }
}

// ── Motor de Chat RAG & Adjuntos ──
async function enviarConsulta() {
  const input = document.getElementById("chat-input");
  const pregunta = input.value.trim();
  if (!pregunta && !currentAttachment) return;

  if (!currentUser) {
    abrirModalAuth();
    return;
  }

  // Ocultar hero
  const hero = document.getElementById("welcome-hero");
  if (hero) hero.style.display = "none";

  const textoPregunta = pregunta || (currentAttachment ? `Por favor, analiza el documento adjunto '${currentAttachment.name}' y emite un dictamen legal.` : "");
  const attachSnapshot = currentAttachment ? { ...currentAttachment } : null;

  // Renderizar mensaje de usuario (con badge de adjunto si existe)
  renderMensajeUsuario(textoPregunta, attachSnapshot ? attachSnapshot.name : null);
  currentMessages.push({ role: "user", content: textoPregunta, adjunto: attachSnapshot ? attachSnapshot.name : null });
  
  input.value = "";
  input.style.height = "auto";
  removeCurrentAttachment();

  // Mostrar mensaje de carga bot con pensamiento animado estilo Claude
  const botRowId = "bot-loading-" + Date.now();
  renderMensajeCarga(botRowId, textoPregunta);

  // Enviar historial previo limpio (sin incluir la pregunta actual)
  const historialPrevio = currentMessages.slice(0, -1).slice(-6);

  try {
    const res = await fetch(`${API_BASE}/chat/consultar`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({
        pregunta: textoPregunta,
        historial: historialPrevio,
        texto_adjunto: attachSnapshot ? attachSnapshot.text : null,
        nombre_adjunto: attachSnapshot ? attachSnapshot.name : null
      })
    });

    const data = await res.json();
    const thoughtHtml = finalizarPensamiento(botRowId);
    
    const loadingRow = document.getElementById(botRowId);
    if (loadingRow) loadingRow.remove();

    if (!res.ok) {
      renderMensajeBot(`⚠️ **Aviso:** ${data.detail || "No se pudo procesar la consulta."}`, [], thoughtHtml);
      return;
    }

    const respuestaTexto = typeof data.respuesta === 'string' ? data.respuesta : (data.respuesta?.respuesta || JSON.stringify(data.respuesta));
    renderMensajeBot(respuestaTexto, data.fuentes || [], thoughtHtml);
    currentMessages.push({ role: "assistant", content: respuestaTexto, fuentes: data.fuentes });

    // Actualizar badge de cuota
    if (data.cuota) {
      updateUserDisplay({ cuota: data.cuota });
    }

    // Auto-guardar chat
    guardarChatActual();
  } catch (err) {
    const thoughtHtml = finalizarPensamiento(botRowId);
    const loadingRow = document.getElementById(botRowId);
    if (loadingRow) loadingRow.remove();
    renderMensajeBot("❌ Error de conexión al consultar el motor RAG de AmmaIA.", [], thoughtHtml);
  }
}

function renderMensajeUsuario(texto, nombreAdjunto = null) {
  const viewport = document.getElementById("chat-viewport");
  const row = document.createElement("div");
  row.className = "message-row user";

  let attachBadge = "";
  if (nombreAdjunto) {
    attachBadge = `<div class="user-attach-badge">📎 Documento adjunto: <strong>${escapeHtml(nombreAdjunto)}</strong></div>`;
  }

  row.innerHTML = `
    <div class="avatar user">👤</div>
    <div class="message-bubble">
      ${attachBadge}
      <p>${escapeHtml(texto)}</p>
    </div>
  `;
  viewport.appendChild(row);
  viewport.scrollTop = viewport.scrollHeight;
}

// ── Almacén y Control de Pensamiento Estilo Claude ──
const activeThinkingSessions = {};

function generarPensamientosLegales(pregunta) {
  const p = (pregunta || "").toLowerCase();
  const thoughts = [
    `Analizando la consulta jurídica formulada por el letrado...`,
    `Delimitando la rama del ordenamiento jurídico español y marco sustantivo aplicable...`
  ];

  if (p.includes("penal") || p.includes("delito") || p.includes("pena") || p.includes("homicidio") || p.includes("asesinato") || p.includes("hurto") || p.includes("robo") || p.includes("estafa") || p.includes("allanamiento") || p.includes("legitima") || p.includes("defensa")) {
    thoughts.push(`Identificando preceptos penales en el Código Penal (LO 10/1995)...`);
    thoughts.push(`Desglosando elementos típicos: tipo objetivo, tipo subjetivo (dolo/imprudencia) y bien jurídico tutelado.`);
    thoughts.push(`Examinando posibles circunstancias modificativas: eximentes (Art. 20 CP), atenuantes (Art. 21 CP) y agravantes (Art. 22 CP).`);
    thoughts.push(`Cotejando jurisprudencia relevante de la Sala 2ª (Penal) del Tribunal Supremo sobre la subsunción típica del hecho.`);
    thoughts.push(`Verificando régimen de penas principales y accesorias, concurso de delitos y reglas de determinación de la pena (Arts. 61 a 72 CP).`);
  } else if (p.includes("civil") || p.includes("contrato") || p.includes("arrendamiento") || p.includes("daño") || p.includes("responsabilidad") || p.includes("1902") || p.includes("clausula") || p.includes("alquiler") || p.includes("lau")) {
    thoughts.push(`Localizando disposiciones en el Código Civil y legislación especial aplicable (LAU / TRLGDCU)...`);
    thoughts.push(`Examinando el principio de autonomía de la voluntad (Art. 1255 CC) y límites imperativos de validez.`);
    thoughts.push(`Analizando presupuestos de responsabilidad: acción/omisión antijurídica, nexo causal y acreditación de daño emergente / lucro cesante.`);
    thoughts.push(`Revisando doctrina consolidada de la Sala 1ª (Civil) del Tribunal Supremo sobre interpretación de cláusulas y nulidad.`);
  } else if (p.includes("laboral") || p.includes("despido") || p.includes("trabajador") || p.includes("empresa") || p.includes("indemniz") || p.includes("et") || p.includes("finiquito")) {
    thoughts.push(`Consultando el Texto Refundido de la Ley del Estatuto de los Trabajadores (RD Leg. 2/2015)...`);
    thoughts.push(`Evaluando causas legales de extinción del contrato y requisitos formales de la carta de despido (Art. 54 y 55 ET).`);
    thoughts.push(`Analizando plazos de caducidad de la acción (20 días hábiles) y trámite preceptivo de conciliación previa ante el SMAC.`);
    thoughts.push(`Revisando doctrina de unificación de doctrina de la Sala 4ª (Social) del Tribunal Supremo.`);
  } else if (p.includes("recurso") || p.includes("plazo") || p.includes("lec") || p.includes("apelacion") || p.includes("casacion") || p.includes("demanda")) {
    thoughts.push(`Consultando la Ley de Enjuiciamiento Civil (Ley 1/2000) y Ley de Enjuiciamiento Criminal (1882)...`);
    thoughts.push(`Verificando presupuestos de admisibilidad, plazos procesales preclusivos y cómputo de días hábiles.`);
    thoughts.push(`Analizando la carga de la prueba (Art. 217 LEC) y proposición de medios probatorios idóneos.`);
  } else {
    thoughts.push(`Recuperando leyes y reglamentos vigentes en la base consolidada del BOE...`);
    thoughts.push(`Comprobando vigencia temporal y posibles reformas legislativas recientes.`);
    thoughts.push(`Analizando antecedentes jurisprudenciales en CENDOJ y resoluciones del Tribunal Constitucional.`);
  }

  thoughts.push(`Articulando la fundamentación técnico-jurídica y estrategia procesal para la defensa letrada.`);
  thoughts.push(`Estructurando el dictamen pericial con citas directas y enlaces exactos a cada artículo del BOE.`);

  return thoughts;
}

function renderMensajeCarga(rowId, pregunta) {
  const viewport = document.getElementById("chat-viewport");
  const row = document.createElement("div");
  row.className = "message-row bot";
  row.id = rowId;
  
  const thoughts = generarPensamientosLegales(pregunta);
  const startTime = Date.now();

  row.innerHTML = `
    <div class="avatar bot">⚖️</div>
    <div class="message-bubble">
      <div class="claude-thought-box" id="thought-box-${rowId}">
        <div class="claude-thought-header" onclick="toggleThoughtBoxDirect(this)">
          <div class="claude-thought-title">
            <span class="thinking-shimmer">🧠 Pensando...</span>
            <span class="claude-thought-meta" id="thought-timer-${rowId}">(0s)</span>
          </div>
          <span class="chevron-icon">▾</span>
        </div>
        <div class="claude-thought-body" id="thought-body-${rowId}">
          <div class="thought-line">› ${escapeHtml(thoughts[0])}</div>
        </div>
      </div>
      <div id="thought-placeholder-${rowId}" style="color: var(--gold-primary); font-size: 13px; display: flex; align-items: center; gap: 8px; margin-top: 6px;">
        <span class="thinking-pulse-dot"></span>
        <span>Consultando BOE, CENDOJ y articulado...</span>
      </div>
    </div>
  `;
  viewport.appendChild(row);
  viewport.scrollTop = viewport.scrollHeight;

  // Temporizador de segundos transcurridos
  const timerInterval = setInterval(() => {
    const timerEl = document.getElementById(`thought-timer-${rowId}`);
    if (timerEl) {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      timerEl.textContent = `(${elapsed}s)`;
    }
  }, 1000);

  // Revelación progresiva de pensamientos
  let thoughtIdx = 1;
  const thoughtsInterval = setInterval(() => {
    const body = document.getElementById(`thought-body-${rowId}`);
    if (body && thoughtIdx < thoughts.length) {
      const line = document.createElement("div");
      line.className = "thought-line";
      line.innerHTML = `› ${escapeHtml(thoughts[thoughtIdx])}`;
      body.appendChild(line);
      body.scrollTop = body.scrollHeight;
      thoughtIdx++;
    }
  }, 350);

  activeThinkingSessions[rowId] = {
    timerInterval,
    thoughtsInterval,
    startTime
  };
}

function finalizarPensamiento(rowId) {
  const session = activeThinkingSessions[rowId];
  if (!session) return "";

  clearInterval(session.timerInterval);
  clearInterval(session.thoughtsInterval);

  const durationSec = Math.max(1, Math.floor((Date.now() - session.startTime) / 1000));
  const timerEl = document.getElementById(`thought-timer-${rowId}`);
  if (timerEl) {
    timerEl.textContent = `(${durationSec} segundos)`;
  }

  const placeholder = document.getElementById(`thought-placeholder-${rowId}`);
  if (placeholder) placeholder.remove();

  const thoughtBox = document.getElementById(`thought-box-${rowId}`);
  if (thoughtBox) {
    const headerTitle = thoughtBox.querySelector(".thinking-shimmer");
    if (headerTitle) {
      headerTitle.className = "";
      headerTitle.innerHTML = `<strong style="color: var(--gold-primary);">🧠 Pensamiento jurídico</strong>`;
    }
    return thoughtBox.outerHTML;
  }
  return "";
}

function toggleThoughtBoxDirect(headerEl) {
  const box = headerEl.closest(".claude-thought-box");
  if (!box) return;
  const body = box.querySelector(".claude-thought-body");
  const chevron = box.querySelector(".chevron-icon");
  if (body) {
    const isCollapsed = body.classList.toggle("collapsed");
    if (chevron) {
      chevron.classList.toggle("collapsed", isCollapsed);
    }
  }
}

function autoEnlazarCitasFrontend(texto) {
  if (!texto) return "";
  let res = String(texto);

  // 1. TJUE / CURIA: Asunto C-154/15, STJUE C-xxx/xx
  res = res.replace(/(?<!\[)(?:STJUE\s+(?:de\s+\d+\s+de\s+\w+\s+de\s+\d+\s+)?(?:Asunto\s+)?(C-\d+\/\d+|T-\d+\/\d+)|(?:Asunto\s+)(C-\d+\/\d+|T-\d+\/\d+))(?!\))/gi, (m, a1, a2) => {
    const num = a1 || a2;
    return `[${m}](https://curia.europa.eu/juris/liste.jsf?num=${encodeURIComponent(num)})`;
  });

  // 2. TEDH / HUDOC: STEDH Lopez Ribalda c. España
  res = res.replace(/(?<!\[)(STEDH\s+(?:de\s+\d+\s+de\s+\w+\s+de\s+\d+\s+)?(?:Asunto\s+)?([A-ZÁÉÍÓÚa-záéíóú\s]+c\.\s+[A-ZÁÉÍÓÚa-záéíóú\s]+))(?!\))/g, (m, full, nombre) => {
    const clean = (nombre || full).replace(/^(?:STEDH|Asunto)\s*/i, '').trim();
    return `[${m}](https://hudoc.echr.coe.int/spa#{"query":["${encodeURIComponent(clean)}"],"documentcollectionid2":["GRANDCHAMBER","CHAMBER"]})`;
  });

  // 3. Tribunal Supremo / CENDOJ: STS 1036/2003, STS 721/2023
  res = res.replace(/(?<!\[)(STS\s+(\d+\/\d+)(?:,\s*de\s*\d+\s*de\s*\w+(?:\s*de\s*\d+)?)?(?:\s*\([^\)]+\))?)(?!\))/g, (m, full, num) => {
    return `[${m}](https://www.poderjudicial.es/search/doSearch?query=${encodeURIComponent('STS ' + num)})`;
  });

  // 4. Tribunal Constitucional: STC 292/2000
  res = res.replace(/(?<!\[)(STC\s+(\d+\/\d+)(?:,\s*de\s*\d+\s*de\s*\w+(?:\s*de\s*\d+)?)?)(?!\))/g, (m, full, num) => {
    return `[${m}](https://hj.tribunalconstitucional.es/es/Resolucion/Buscar?texto=${encodeURIComponent(num)})`;
  });

  return res;
}

function getPillIcon(norma, esJurisprudencia) {
  const n = (norma || "").toUpperCase();
  if (n.includes("TEDH") || n.includes("HUDOC") || n.includes("TJUE") || n.includes("CURIA") || n.includes("EUROPEO")) return "🇪🇺";
  if (n.includes("CONSTITUCIONAL") || n.includes("STC")) return "⚖️";
  if (esJurisprudencia || n.includes("SUPREMO") || n.includes("STS") || n.includes("AUDIENCIA")) return "🏛️";
  return "📜";
}

function renderMensajeBot(markdownTexto, fuentes = [], existingThoughtHtml = "") {
  const viewport = document.getElementById("chat-viewport");
  const row = document.createElement("div");
  row.className = "message-row bot";

  let safeText = "";
  if (typeof markdownTexto === "string") {
    safeText = markdownTexto;
  } else if (markdownTexto && typeof markdownTexto === "object") {
    safeText = markdownTexto.respuesta || JSON.stringify(markdownTexto, null, 2);
  } else {
    safeText = String(markdownTexto || "");
  }

  // Enriquecer cualquier cita jurídica huérfana con enlaces directos
  const textoEnriquecido = autoEnlazarCitasFrontend(safeText);
  const parsedHtml = marked.parse(textoEnriquecido);

  let citationsHtml = "";
  if (fuentes && fuentes.length > 0) {
    citationsHtml = `
      <div class="citations-box">
        <div class="citations-title"><span>📜</span> Fuentes Legales y Precedentes Citados:</div>
        <div style="display: flex; flex-wrap: wrap; gap: 6px;">
          ${fuentes.map(f => `
            <a href="${f.url}" target="_blank" rel="noopener" class="citation-pill" title="${f.materia || ''}">
              <span>${getPillIcon(f.norma, f.es_jurisprudencia)}</span>
              <span><strong>${escapeHtml(f.norma)}</strong> ${escapeHtml(f.articulo || '')}</span>
            </a>
          `).join('')}
        </div>
      </div>
    `;
  }

  row.innerHTML = `
    <div class="avatar bot">⚖️</div>
    <div class="message-bubble">
      ${existingThoughtHtml}
      ${parsedHtml}
      ${citationsHtml}
      <div class="msg-actions">
        <button class="btn-msg-action" onclick="exportarMensajePDF(this)">📕 Descargar PDF</button>
        <button class="btn-msg-action" onclick="exportarMensajeWord(this)">📄 Descargar Word</button>
        <button class="btn-msg-action" onclick="copiarTexto(this)">📋 Copiar</button>
      </div>
    </div>
  `;
  viewport.appendChild(row);
  viewport.scrollTop = viewport.scrollHeight;
}

function nuevoChat() {
  currentChatId = null;
  currentMessages = [];
  removeCurrentAttachment();
  document.getElementById("chat-viewport").innerHTML = "";
  
  // Quitar resaltado de todos los chats del historial
  document.querySelectorAll("#chat-history-list .chat-history-item").forEach(el => el.classList.remove("active"));

  const viewport = document.getElementById("chat-viewport");
  viewport.innerHTML = `
    <div class="welcome-hero" id="welcome-hero">
      <div class="hero-icon">⚖️</div>
      <h2 class="hero-title">AmmaIA Jurídica</h2>
      <p class="hero-desc">
        Asistente de Inteligencia Artificial especializado en el Ordenamiento Jurídico Español y Derecho Europeo.
        Consultas fundamentadas en el <strong>BOE, Códigos Consolidados, Jurisprudencia del Tribunal Supremo (CENDOJ), TEDH (HUDOC) y TJUE (CURIA)</strong> con trazabilidad y citas exactas.
        Puedes adjuntar contratos, demandas y sentencias en <strong>PDF, Word o TXT</strong> con el botón 📎.
      </p>
      <div class="prompt-chips-grid">
        <div class="prompt-chip" data-query="¿Qué requisitos exige el artículo 20.4 del Código Penal para apreciar la eximente completa de Legítima Defensa?">
          ⚖️ <strong>Legítima Defensa (Art. 20.4 CP)</strong>
          <div style="font-size: 11px; color: var(--text-dim); margin-top: 4px;">Requisitos y jurisprudencia del TS</div>
        </div>
        <div class="prompt-chip" data-query="Explícame la diferencia entre el delito de hurto (Art. 234 CP) y robo con fuerza (Art. 238 CP) según la jurisprudencia consolidada.">
          📜 <strong>Hurto vs. Robo con Fuerza</strong>
          <div style="font-size: 11px; color: var(--text-dim); margin-top: 4px;">Artículos 234 y 238 CP y penalidad</div>
        </div>
        <div class="prompt-chip" data-query="¿Cuáles son los plazos y causas para impugnar un despido disciplinario y calcular la indemnización por despido improcedente según el Estatuto de los Trabajadores?">
          💼 <strong>Despido Disciplinario (ET)</strong>
          <div style="font-size: 11px; color: var(--text-dim); margin-top: 4px;">Art. 54 y 56 Estatuto Trabajadores</div>
        </div>
        <div class="prompt-chip" data-query="¿Cómo se computan los plazos para interponer recurso de apelación civil según el artículo 448 de la Ley de Enjuiciamiento Civil?">
          🏛️ <strong>Recursos en la LEC (Art. 448)</strong>
          <div style="font-size: 11px; color: var(--text-dim); margin-top: 4px;">Plazos y cómputo procesal</div>
        </div>
      </div>
    </div>
  `;
  document.getElementById("current-chat-title").textContent = "Nueva Consulta";

  document.querySelectorAll(".prompt-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const q = chip.getAttribute("data-query");
      if (q) {
        document.getElementById("chat-input").value = q;
        enviarConsulta();
      }
    });
  });
}

async function guardarChatActual() {
  if (!currentMessages.length || !currentUser) return;
  if (!currentChatId) {
    const primerTexto = currentMessages[0].content;
    const titulo = primerTexto.slice(0, 28) + (primerTexto.length > 28 ? "..." : "");
    currentChatId = "chat_" + Date.now();
    document.getElementById("current-chat-title").textContent = titulo;
  }

  const titulo = document.getElementById("current-chat-title").textContent;
  try {
    await fetch(`${API_BASE}/chat/guardar`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({
        chat_id: currentChatId,
        titulo: titulo,
        mensajes: currentMessages
      })
    });
    cargarHistorial();
  } catch (err) {
    console.error("Error guardando chat:", err);
  }
}

async function cargarHistorial() {
  if (!currentUser) return;
  try {
    const res = await fetch(`${API_BASE}/chat/historial`, {
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    if (!res.ok) return;
    const data = await res.json();
    const listEl = document.getElementById("chat-history-list");
    listEl.innerHTML = "";

    data.chats.forEach(c => {
      const item = document.createElement("div");
      item.setAttribute("data-chat-id", c.id);
      item.className = `chat-history-item ${c.id === currentChatId ? 'active' : ''}`;
      item.innerHTML = `
        <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 190px; cursor: pointer;">💬 ${escapeHtml(c.titulo)}</span>
        <button class="del-btn" title="Eliminar consulta">✕</button>
      `;

      item.addEventListener("click", (e) => {
        if (e.target.classList.contains("del-btn")) return;
        restaurarChat(c);
      });

      item.querySelector(".del-btn").addEventListener("click", (e) => {
        e.stopPropagation();
        borrarChat(c.id);
      });

      listEl.appendChild(item);
    });
  } catch (err) {
    console.error("Error cargando historial:", err);
  }
}

function restaurarChat(c) {
  currentChatId = c.id;
  currentMessages = c.mensajes || [];
  document.getElementById("current-chat-title").textContent = c.titulo;
  
  // Resaltar exactamente el chat clickeado en la barra lateral
  document.querySelectorAll("#chat-history-list .chat-history-item").forEach(el => {
    el.classList.toggle("active", el.getAttribute("data-chat-id") === c.id);
  });

  const viewport = document.getElementById("chat-viewport");
  viewport.innerHTML = "";

  currentMessages.forEach(m => {
    if (m.role === "user") {
      renderMensajeUsuario(m.content, m.adjunto || null);
    } else {
      renderMensajeBot(m.content, m.fuentes || []);
    }
  });
}

async function borrarChat(chatId) {
  if (!confirm("¿Deseas eliminar este dictamen del historial?")) return;
  try {
    await fetch(`${API_BASE}/chat/${chatId}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    if (currentChatId === chatId) {
      nuevoChat();
    }
    cargarHistorial();
  } catch (err) {
    console.error("Error borrando chat:", err);
  }
}

// ── Exportación a PDF y Word ──
async function exportarDictamenPDF(mensajesCustom = null) {
  const msgs = mensajesCustom || currentMessages;
  if (!msgs.length) {
    alert("No hay consultas en la sesión actual para exportar a PDF.");
    return;
  }
  const titulo = document.getElementById("current-chat-title").textContent || "Dictamen AmmaIA";
  try {
    const res = await fetch(`${API_BASE}/chat/exportar-pdf`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({
        titulo: titulo,
        mensajes: msgs
      })
    });

    if (!res.ok) {
      alert("Error al generar el archivo PDF.");
      return;
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Dictamen_AmmaIA_${Date.now()}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch (err) {
    alert("Error de conexión al exportar PDF.");
  }
}

async function exportarDictamenWord(mensajesCustom = null) {
  const msgs = mensajesCustom || currentMessages;
  if (!msgs.length) {
    alert("No hay consultas en la sesión actual para exportar a Word.");
    return;
  }
  const titulo = document.getElementById("current-chat-title").textContent || "Dictamen AmmaIA";
  try {
    const res = await fetch(`${API_BASE}/chat/exportar-word`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({
        titulo: titulo,
        mensajes: msgs
      })
    });

    if (!res.ok) {
      alert("Error al generar el archivo Word.");
      return;
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Dictamen_AmmaIA_${Date.now()}.docx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch (err) {
    alert("Error de conexión al exportar Word.");
  }
}

function exportarMensajePDF(btn) {
  const bubble = btn.closest(".message-bubble");
  const txt = bubble.innerText;
  exportarDictamenPDF([{ role: "assistant", content: txt }]);
}

function exportarMensajeWord(btn) {
  const bubble = btn.closest(".message-bubble");
  const txt = bubble.innerText;
  exportarDictamenWord([{ role: "assistant", content: txt }]);
}

// ── Panel Maestro de Administración & Inspector del Servidor ──
async function abrirModalAdmin() {
  document.getElementById("modal-admin").classList.add("active");
  switchAdminTab("metrics");
}

function switchAdminTab(tab) {
  // Botones
  document.querySelectorAll("[id^='btn-tab-admin-']").forEach(btn => btn.classList.remove("active"));
  const activeBtn = document.getElementById(`btn-tab-admin-${tab}`);
  if (activeBtn) activeBtn.classList.add("active");

  // Vistas
  document.querySelectorAll(".admin-tab-view").forEach(v => v.style.display = "none");
  const view = document.getElementById(`admin-view-${tab}`);
  if (view) view.style.display = "block";

  if (tab === "metrics") cargarMetricasAdmin();
  else if (tab === "users") cargarUsuariosAdmin();
  else if (tab === "chats") cargarChatsAdmin();
  else if (tab === "bans") cargarBansAdmin();
  else if (tab === "raw") cargarRawAdmin();
}

let currentRawServerData = null;

async function cargarRawAdmin() {
  const container = document.getElementById("admin-raw-container");
  if (!container) return;
  container.textContent = "Obteniendo volcado RAW en tiempo real del servidor SQLite y Vector Index...";

  try {
    const res = await fetch(`${API_BASE}/admin/raw-dump`, {
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    if (!res.ok) {
      container.textContent = "Error al obtener volcado RAW del servidor.";
      return;
    }
    const data = await res.json();
    currentRawServerData = data;
    container.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    container.textContent = "Error de conexión obteniendo datos RAW.";
  }
}

function copiarRawJson() {
  if (!currentRawServerData) {
    alert("No hay datos RAW cargados todavía.");
    return;
  }
  navigator.clipboard.writeText(JSON.stringify(currentRawServerData, null, 2));
  alert("📋 JSON RAW copiado al portapapeles con éxito.");
}

function descargarRawJson() {
  if (!currentRawServerData) {
    alert("No hay datos RAW cargados todavía.");
    return;
  }
  const blob = new Blob([JSON.stringify(currentRawServerData, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `AmmaIA_Server_RAW_Dump_${new Date().toISOString().slice(0,10)}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function cargarMetricasAdmin() {
  try {
    const res = await fetch(`${API_BASE}/admin/metricas`, {
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    if (!res.ok) return;
    const m = await res.json();
    document.getElementById("metric-total-users").textContent = m.total_usuarios || "0";
    document.getElementById("metric-total-premium").textContent = m.total_premium || "0";
    document.getElementById("metric-queries-today").textContent = m.consultas_hoy || "0";
    document.getElementById("metric-rag-chunks").textContent = m.total_chunks_rag || "0";
    document.getElementById("metric-total-bans").textContent = m.total_bans || "0";
    document.getElementById("metric-db-size").textContent = m.db_size_kb || "0 KB";
  } catch (err) {
    console.error("Error cargando métricas:", err);
  }
}

async function cargarChatsAdmin() {
  const tbody = document.getElementById("admin-chats-tbody");
  tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 20px;">Cargando registro de consultas...</td></tr>`;

  try {
    const res = await fetch(`${API_BASE}/admin/auditoria-chats`, {
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    if (!res.ok) {
      tbody.innerHTML = `<tr><td colspan="6" style="color: var(--danger); text-align: center;">Error al cargar auditoría.</td></tr>`;
      return;
    }
    const data = await res.json();
    tbody.innerHTML = "";

    if (!data.chats || data.chats.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 20px;">No hay consultas archivadas en el servidor.</td></tr>`;
      return;
    }

    data.chats.forEach(c => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-family: monospace; font-size: 11px; color: var(--gold-primary);">${escapeHtml(c.chat_id)}</td>
        <td>
          <strong>${escapeHtml(c.user_nombre)}</strong><br>
          <span style="font-size: 11px; color: var(--text-dim);">${escapeHtml(c.user_email)} (ID: ${c.user_id})</span>
        </td>
        <td style="font-size: 11px; color: var(--text-muted);">${escapeHtml(c.fecha.replace('T', ' ').slice(0, 19))}</td>
        <td style="font-weight: 600; color: var(--text-main);">${escapeHtml(c.titulo)}</td>
        <td style="text-align: center;"><span class="user-role-badge">${c.num_mensajes} msgs</span></td>
        <td style="font-size: 11px; color: var(--cyan-primary);">
          ${escapeHtml(c.contenido_seguro)}
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="color: var(--danger); text-align: center;">Error de conexión con el servidor.</td></tr>`;
  }
}

async function cargarBansAdmin() {
  const tbody = document.getElementById("admin-bans-tbody");
  tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 20px;">Cargando lista negra de sanciones...</td></tr>`;

  try {
    const res = await fetch(`${API_BASE}/admin/bans-activos`, {
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    if (!res.ok) {
      tbody.innerHTML = `<tr><td colspan="6" style="color: var(--danger); text-align: center;">Error al cargar sanciones.</td></tr>`;
      return;
    }
    const data = await res.json();
    tbody.innerHTML = "";

    if (!data.bans || data.bans.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--success); padding: 20px;">✓ No hay sanciones activas en el servidor.</td></tr>`;
      return;
    }

    data.bans.forEach(b => {
      const tr = document.createElement("tr");
      const tipoIcon = b.tipo === 'usuario' ? '⛔ Cuenta' : (b.tipo === 'ip' ? '🌐 IP' : '💻 Hardware (HWID)');
      tr.innerHTML = `
        <td>#${b.id}</td>
        <td><strong style="color: var(--danger);">${escapeHtml(b.target)}</strong></td>
        <td><span class="user-role-badge" style="border-color: var(--danger); color: var(--danger);">${tipoIcon}</span></td>
        <td style="font-size: 12px; color: var(--text-muted);">${escapeHtml(b.motivo)}</td>
        <td style="font-size: 11px; color: var(--text-dim);">${escapeHtml(b.fecha_ban.replace('T', ' ').slice(0, 19))}</td>
        <td>
          <button class="btn-secondary" style="color: var(--success); font-size: 10px; padding: 3px 8px;" onclick="unbanUser('${b.target}', '${b.tipo}')">✅ Desbloquear</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="color: var(--danger); text-align: center;">Error de conexión.</td></tr>`;
  }
}

async function cargarUsuariosAdmin() {
  const tbody = document.getElementById("admin-users-tbody");
  tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 20px;">Cargando usuarios...</td></tr>`;

  try {
    const res = await fetch(`${API_BASE}/admin/usuarios`, {
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    if (!res.ok) {
      tbody.innerHTML = `<tr><td colspan="6" style="color: var(--danger); text-align: center;">Error al cargar usuarios.</td></tr>`;
      return;
    }

    const data = await res.json();
    tbody.innerHTML = "";

    data.usuarios.forEach(u => {
      const tr = document.createElement("tr");

      // Badges de estado de sanción
      let banStatusHtml = "";
      if (u.is_banned_user) banStatusHtml += `<span style="background: rgba(239, 68, 68, 0.2); color: var(--danger); font-size: 10px; padding: 2px 6px; border-radius: 4px; display: inline-block; margin-bottom: 2px;">⛔ Cuenta Baneada</span><br>`;
      if (u.is_banned_ip) banStatusHtml += `<span style="background: rgba(245, 158, 11, 0.2); color: var(--gold-primary); font-size: 10px; padding: 2px 6px; border-radius: 4px; display: inline-block; margin-bottom: 2px;">🌐 IP Baneada</span><br>`;
      if (u.is_banned_hwid) banStatusHtml += `<span style="background: rgba(168, 85, 247, 0.2); color: #c084fc; font-size: 10px; padding: 2px 6px; border-radius: 4px; display: inline-block; margin-bottom: 2px;">💻 HWID Bloqueado</span><br>`;

      tr.innerHTML = `
        <td>#${u.id}</td>
        <td>
          <strong>${escapeHtml(u.nombre)}</strong><br>
          <span style="color: var(--text-dim); font-size: 11px;">${escapeHtml(u.email)}</span>
          <div style="margin-top: 4px;">${banStatusHtml}</div>
        </td>
        <td><span class="user-role-badge">${escapeHtml(u.rol)}</span></td>
        <td style="font-size: 11px; color: var(--text-dim);">
          <strong>IP:</strong> ${escapeHtml(u.last_ip || 'N/D')}<br>
          <strong>HWID:</strong> ${escapeHtml((u.hwid || 'N/D').slice(0, 12))}...
        </td>
        <td>
          <label class="switch">
            <input type="checkbox" ${u.is_premium ? 'checked' : ''} onchange="togglePremiumUser(${u.id}, this.checked)">
            <span class="slider"></span>
          </label>
        </td>
        <td>
          <div style="display: flex; flex-direction: column; gap: 4px; min-width: 140px;">
            <!-- Ban Cuenta -->
            ${u.is_banned_user ? 
              `<button class="btn-secondary" style="color: var(--success); font-size: 10px; padding: 3px 6px;" onclick="unbanUser('${u.email}', 'usuario')">✅ Quitar Ban Cuenta</button>` :
              `<button class="btn-secondary" style="color: var(--danger); font-size: 10px; padding: 3px 6px;" onclick="promptBanUser('${u.email}', 'usuario')">⛔ Banear Cuenta</button>`
            }
            
            <!-- Ban IP -->
            ${u.last_ip ? (u.is_banned_ip ? 
              `<button class="btn-secondary" style="color: var(--success); font-size: 10px; padding: 3px 6px;" onclick="unbanUser('${u.last_ip}', 'ip')">✅ Quitar Ban IP</button>` :
              `<button class="btn-secondary" style="color: var(--gold-primary); font-size: 10px; padding: 3px 6px;" onclick="promptBanUser('${u.last_ip}', 'ip')">🌐 Banear IP (${escapeHtml(u.last_ip)})</button>`) : ''
            }

            <!-- Ban HWID -->
            ${u.hwid ? (u.is_banned_hwid ? 
              `<button class="btn-secondary" style="color: var(--success); font-size: 10px; padding: 3px 6px;" onclick="unbanUser('${u.hwid}', 'hwid')">✅ Quitar Ban HWID</button>` :
              `<button class="btn-secondary" style="color: #c084fc; font-size: 10px; padding: 3px 6px;" onclick="promptBanUser('${u.hwid}', 'hwid')">💻 HWID Ban (Hardware)</button>`) : ''
            }

            <!-- Triple Ban -->
            <button class="btn-secondary" style="color: #ef4444; font-size: 9px; padding: 2px 4px; border-color: rgba(239,68,68,0.4);" onclick="tripleBanUser('${u.email}', '${u.last_ip || ''}', '${u.hwid || ''}')">💥 Triple Ban</button>

            <!-- Borrar Usuario Definitivo -->
            <button class="btn-secondary" style="color: #f87171; font-size: 9px; padding: 2px 4px; border-color: rgba(239,68,68,0.6);" onclick="confirmarEliminarUsuarioAdmin(${u.id}, '${escapeHtml(u.email)}')">🗑️ Borrar Usuario</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="color: var(--danger); text-align: center;">Error de conexión.</td></tr>`;
  }
}

async function togglePremiumUser(userId, isPremium) {
  try {
    const res = await fetch(`${API_BASE}/admin/toggle-premium`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({ user_id: userId, is_premium: isPremium })
    });
    const data = await res.json();
    if (!res.ok) alert(data.detail || "Error al actualizar estado Premium.");
  } catch (err) {
    alert("Error de conexión con el servidor.");
  }
}

async function promptBanUser(target, tipo = 'usuario') {
  if (!target) {
    alert("No se dispone del dato para aplicar esta sanción.");
    return;
  }
  const motivo = prompt(`Motivo de la sanción de ${tipo.toUpperCase()} para '${target}':`, "Infracción de términos legales");
  if (!motivo) return;

  try {
    const res = await fetch(`${API_BASE}/admin/ban`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({ target: target, tipo: tipo, motivo: motivo })
    });
    if (res.ok) {
      cargarUsuariosAdmin();
    } else {
      const data = await res.json();
      alert(data.detail || "Error aplicando sanción.");
    }
  } catch (err) {
    alert("Error al aplicar sanción.");
  }
}

async function tripleBanUser(email, ip, hwid) {
  const motivo = prompt(`Motivo del TRIPLE BAN TOTAL (Cuenta + IP + Hardware) para '${email}':`, "Sanción disciplinaria máxima");
  if (!motivo) return;

  try {
    // 1. Ban Cuenta
    await fetch(`${API_BASE}/admin/ban`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${currentToken}` },
      body: JSON.stringify({ target: email, tipo: "usuario", motivo: motivo })
    });

    // 2. Ban IP
    if (ip) {
      await fetch(`${API_BASE}/admin/ban`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${currentToken}` },
        body: JSON.stringify({ target: ip, tipo: "ip", motivo: motivo })
      });
    }

    // 3. Ban HWID
    if (hwid) {
      await fetch(`${API_BASE}/admin/ban`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${currentToken}` },
        body: JSON.stringify({ target: hwid, tipo: "hwid", motivo: motivo })
      });
    }

    alert(`💥 Triple Ban aplicado con éxito a ${email}.`);
    cargarUsuariosAdmin();
  } catch (err) {
    alert("Error aplicando triple ban.");
  }
}

async function unbanUser(target, tipo) {
  try {
    await fetch(`${API_BASE}/admin/unban`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({ target, tipo })
    });
    cargarUsuariosAdmin();
  } catch (err) {
    alert("Error al revocar sanción.");
  }
}

async function confirmarEliminarUsuarioAdmin(userId, email) {
  const confirmacion = confirm(`¿Estás seguro de que deseas eliminar definitivamente al usuario #${userId} (${email}) y todos sus dictámenes?`);
  if (!confirmacion) return;

  try {
    const res = await fetch(`${API_BASE}/admin/usuario/${userId}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    const data = await res.json();
    if (res.ok) {
      alert(data.mensaje || "Usuario eliminado.");
      cargarUsuariosAdmin();
    } else {
      alert(data.detail || "Error al eliminar usuario.");
    }
  } catch (err) {
    alert("Error al conectar con el servidor.");
  }
}

// ── Modal BOE ──
async function abrirModalBoe() {
  document.getElementById("modal-boe").classList.add("active");
  const container = document.getElementById("boe-content-list");
  container.innerHTML = `<div style="color: var(--gold-primary);">Consultando sumario oficial del BOE...</div>`;

  try {
    const res = await fetch(`${API_BASE}/boe/hoy`);
    const data = await res.json();
    container.innerHTML = `
      <div style="margin-bottom: 12px; font-size: 13px; color: var(--cyan-primary);">
        📅 Sumario Oficial del <strong>${data.fecha}</strong> (${data.total_publicadas} disposiciones publicadas, ${data.total_relevantes} relevantes):
      </div>
      <div style="display: flex; flex-direction: column; gap: 8px;">
        ${data.leyes.map(l => `
          <div style="background: var(--bg-card-light); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 10px 14px;">
            <div style="font-size: 13px; font-weight: 600; color: var(--text-main); margin-bottom: 4px;">${escapeHtml(l.titulo)}</div>
            <div style="display: flex; gap: 10px; font-size: 11px;">
              <a href="${l.url_web}" target="_blank" rel="noopener" style="color: var(--gold-primary);">🌐 Ver en BOE.es</a>
              ${l.url_pdf ? `<a href="${l.url_pdf}" target="_blank" rel="noopener" style="color: var(--cyan-primary);">📄 Descargar PDF Oficial</a>` : ''}
            </div>
          </div>
        `).join('')}
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color: var(--danger);">No se pudo conectar con el servicio del BOE.</div>`;
  }
}

// ── Helpers ──
function escapeHtml(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function copiarTexto(btn) {
  const bubble = btn.closest(".message-bubble");
  const p = bubble.innerText;
  navigator.clipboard.writeText(p);
  btn.textContent = "✓ Copiado";
  setTimeout(() => btn.textContent = "📋 Copiar", 2000);
}
