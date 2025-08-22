document.addEventListener("DOMContentLoaded", function () {
  // =====================
  // ELEMENTOS BASE
  // =====================
  const modoTransporte = document.getElementById("modoTransporte");

  // Detalles de viaje
  const vueloOrigenPais    = document.getElementById("vueloOrigenPais");
  const vueloOrigenCiudad  = document.getElementById("vueloOrigenCiudad");
  const vueloDestinoPais   = document.getElementById("vueloDestinoPais");
  const vueloDestinoCiudad = document.getElementById("vueloDestinoCiudad");

  // Selects de "aeropuerto / puerto" (reutilizados según modo)
  const selectAeropuertoOrigen  = document.getElementById("id_aeropuerto_origen");
  const selectAeropuertoDestino = document.getElementById("id_aeropuerto_destino");

  // Ruta (producto)
  const paisOrigenRuta    = document.getElementById("paisOrigen");
  const ciudadOrigenRuta  = document.getElementById("ciudadOrigen");
  const paisDestinoRuta   = document.getElementById("paisDestino");
  const ciudadDestinoRuta = document.getElementById("ciudadDestino");

  // Mapa de países: ISO-2 -> Nombre
  const paisesMap = {};

  // Etiquetas dinámicas
  const labelTransporte = document.getElementById("label_nombre_transporte");

  // =====================
  // GRUPOS DE EMBALAJE
  // =====================
  // Aéreo
  const grupoAereo        = document.getElementById("grupo_embalaje_aereo");
  const tipoEmbalajeAereo = document.getElementById("tipoEmbalajeAereo");
  const grupoOtroAereo    = document.getElementById("grupo_otro_embalaje_aereo");
  // Marítimo
  const grupoMaritimo        = document.getElementById("grupo_embalaje_maritimo");
  const embalajeMaritimo     = document.getElementById("embalajeMaritimo");
  const grupoTipoContenedor  = document.getElementById("grupo_tipo_container_maritimo");
  const tipoContainer        = document.getElementById("tipoContainerMaritimo");
  const grupoEmbalajeLCL     = document.getElementById("grupo_tipo_embalaje_maritimo_lcl");
  const embalajeLCL          = document.getElementById("tipoEmbalajeLCL");
  const grupoOtroLCL         = document.getElementById("grupo_otro_embalaje_lcl");
  // Terrestre
  const grupoTerrestre        = document.getElementById("grupo_embalaje_terrestre");
  const tipoEmbalajeTerrestre = document.getElementById("tipoEmbalajeTerrestre");
  const grupoOtroTerrestre    = document.getElementById("grupo_otro_embalaje_terrestre");

  // =====================
  // UTILS
  // =====================
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + "=")) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // =====================
  // CARGA DE PAISES / CIUDADES / AEROPUERTOS / PUERTOS
  // =====================
  function cargarPaises() {
    fetch("/api/paises/")
      .then(r => r.json())
      .then(data => {
        const lista = data.paises || [];
        lista.forEach(pais => {
          // Guardamos el nombre por ISO-2
          paisesMap[pais.codigo] = pais.nombre;

          // Crea options (value: ISO-2, text: nombre)
          const optO  = new Option(pais.nombre, pais.codigo);
          const optD  = new Option(pais.nombre, pais.codigo);
          const optRO = new Option(pais.nombre, pais.codigo);
          const optRD = new Option(pais.nombre, pais.codigo);

          if (vueloOrigenPais)  vueloOrigenPais.appendChild(optO);
          if (vueloDestinoPais) vueloDestinoPais.appendChild(optD);
          if (paisOrigenRuta)   paisOrigenRuta.appendChild(optRO);
          if (paisDestinoRuta)  paisDestinoRuta.appendChild(optRD);
        });
      })
      .catch(err => console.error("Error cargando países:", err));
  }

  function cargarCiudades(nombrePais, select) {
    if (!nombrePais || !select) return;
    select.innerHTML = '<option value="">Cargando ciudades...</option>';
    fetch("/api/ciudades/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
      body: JSON.stringify({ pais: nombrePais })
    })
    .then(res => res.json())
    .then(data => {
      select.innerHTML = '<option value="">Seleccione una ciudad</option>';
      (data.ciudades || []).forEach(ciudad => {
        select.appendChild(new Option(ciudad, ciudad));
      });
    })
    .catch(() => { select.innerHTML = '<option value="">Error al cargar</option>'; });
  }

  // >>>> Cambiada: recibe ISO-2 y envía {pais, pais_code}
  function cargarAeropuertos(codigoPais, select) {
    if (!codigoPais || !select) return;
    const nombrePais = paisesMap[codigoPais] || "";
    select.innerHTML = '<option value="">Cargando aeropuertos...</option>';
    fetch("/api/aeropuertos/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
      body: JSON.stringify({ pais: nombrePais, pais_code: codigoPais })
    })
    .then(res => res.json())
    .then(data => {
      select.innerHTML = '<option value="">Seleccione un aeropuerto</option>';
      (data.aeropuertos || []).forEach(a => {
        select.appendChild(new Option(`${a.name} (${a.city})`, a.iata));
      });
    })
    .catch(() => { select.innerHTML = '<option value="">Error al cargar</option>'; });
  }

  // >>>> Cambiada: recibe ISO-2 y envía {pais, pais_code, function: "1"}
  function cargarPuertos(codigoPais, select) {
    if (!codigoPais || !select) return;
    const nombrePais = paisesMap[codigoPais] || "";
    select.innerHTML = '<option value="">Cargando puertos...</option>';
    fetch("/api/unlocode/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
      body: JSON.stringify({ pais: codigoPais, function: "1" })
    })
    .then(res => res.json())
    .then(data => {
      select.innerHTML = '<option value="">Seleccione un puerto</option>';
      (data.ubicaciones || []).forEach(p => {
        select.appendChild(new Option(`${p.name} (${p.locode})`, p.locode));
      });
    })
    .catch(() => { select.innerHTML = '<option value="">Error al cargar</option>'; });
  }
// --- Helpers de banderas ---
const FLAG_CDN_BASE = 'https://flagcdn.com/24x18/'; // puedes subir a 36x27 si quieres
function flagUrl(code){ return `${FLAG_CDN_BASE}${(code||'').toLowerCase()}.png`; }

// Fallback emoji 🇨🇱 a partir de ISO2 (por si la imagen falla)
function isoToFlagEmoji(iso2){
  if(!iso2 || iso2.length !== 2) return '';
  const A = 0x1F1E6, base = 'A'.charCodeAt(0);
  return String.fromCodePoint(
    A + (iso2[0].toUpperCase().charCodeAt(0) - base),
    A + (iso2[1].toUpperCase().charCodeAt(0) - base)
  );
}

// Plantilla Select2 para mostrar banderita + nombre
function formatCountry(state){
  if(!state.id) return state.text;
  const code = (state.element?.dataset.code || state.id || '').toUpperCase();
  if(!code) return state.text;

  const emoji = isoToFlagEmoji(code);
  const html = `
    <span class="country-option">
      <img class="flag" src="${flagUrl(code)}"
           onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-block';">
      <span style="display:none;margin-right:8px;">${emoji}</span>${state.text}
    </span>`;
  // Select2 necesita que devolvamos HTML sin escapar
  return html;
}

// Inicializa Select2 con la plantilla (idempotente)
function initCountrySelects(){
  if (typeof $ === 'undefined' || !$.fn.select2) return; // por si no está Select2 en esta vista
  const $targets = $('#vueloOrigenPais, #vueloDestinoPais, #paisOrigen, #paisDestino');
  $targets.each(function(){
    const $el = $(this);
    if ($el.data('select2')) { $el.select2('destroy'); }
    $el.select2({
      width: '100%',
      placeholder: 'Seleccione un país',
      allowClear: true,
      templateResult: formatCountry,
      templateSelection: formatCountry,
      escapeMarkup: m => m // ¡importante! para que se renderice la imagen
    });
  });
}

  // =====================
  // EVENTOS: DETALLES DE VIAJE
  // =====================
  if (vueloOrigenPais) {
    vueloOrigenPais.addEventListener("change", () => {
      const codigo = vueloOrigenPais.value;               // ISO-2
      const nombre = paisesMap[codigo] || "";
      if (vueloOrigenCiudad) cargarCiudades(nombre, vueloOrigenCiudad);

      const modo = (modoTransporte && modoTransporte.value) || "";
      if (modo === "Aereo") {
        cargarAeropuertos(codigo, selectAeropuertoOrigen);
      } else if (modo === "Maritimo") {
        cargarPuertos(codigo, selectAeropuertoOrigen);
      } else if (selectAeropuertoOrigen) {
        selectAeropuertoOrigen.innerHTML = '<option value="">Seleccione una opción</option>';
      }
    });
  }

  if (vueloDestinoPais) {
    vueloDestinoPais.addEventListener("change", () => {
      const codigo = vueloDestinoPais.value;              // ISO-2
      const nombre = paisesMap[codigo] || "";
      if (vueloDestinoCiudad) cargarCiudades(nombre, vueloDestinoCiudad);

      const modo = (modoTransporte && modoTransporte.value) || "";
      if (modo === "Aereo") {
        cargarAeropuertos(codigo, selectAeropuertoDestino);
      } else if (modo === "Maritimo") {
        cargarPuertos(codigo, selectAeropuertoDestino);
      } else if (selectAeropuertoDestino) {
        selectAeropuertoDestino.innerHTML = '<option value="">Seleccione una opción</option>';
      }
    });
  }

  // =====================
  // EVENTOS: RUTA (PRODUCTO) -> CIUDADES
  // =====================
  if (paisOrigenRuta && ciudadOrigenRuta) {
    paisOrigenRuta.addEventListener("change", () => {
      const nombre = paisesMap[paisOrigenRuta.value] || paisOrigenRuta.options[paisOrigenRuta.selectedIndex]?.textContent || "";
      cargarCiudades(nombre, ciudadOrigenRuta);
    });
  }
  if (paisDestinoRuta && ciudadDestinoRuta) {
    paisDestinoRuta.addEventListener("change", () => {
      const nombre = paisesMap[paisDestinoRuta.value] || paisDestinoRuta.options[paisDestinoRuta.selectedIndex]?.textContent || "";
      cargarCiudades(nombre, ciudadDestinoRuta);
    });
  }

  // =====================
  // VISTA DE EMBALAJE + ETIQUETAS
  // =====================
  function actualizarVistaEmbalaje() {
    const valorModo = (modoTransporte && modoTransporte.value) || "";

    // Oculta todo
    [grupoAereo, grupoOtroAereo, grupoMaritimo, grupoTipoContenedor,
     grupoEmbalajeLCL, grupoOtroLCL, grupoTerrestre, grupoOtroTerrestre]
      .forEach(e => { if (e) e.classList.add("d-none"); });

    if (!labelTransporte) return;

    if (valorModo === "Aereo") {
      labelTransporte.textContent = "Nombre Avión / Línea Aérea";
      if (grupoAereo) grupoAereo.classList.remove("d-none");
      if (tipoEmbalajeAereo && tipoEmbalajeAereo.value === "OTRO") {
        if (grupoOtroAereo) grupoOtroAereo.classList.remove("d-none");
      }
    } else if (valorModo === "Maritimo") {
      labelTransporte.textContent = "Nombre Navío / Línea Naviera";
      if (grupoMaritimo) grupoMaritimo.classList.remove("d-none");
      if (embalajeMaritimo) {
        if (embalajeMaritimo.value === "FCL") {
          if (grupoTipoContenedor) grupoTipoContenedor.classList.remove("d-none");
        } else if (embalajeMaritimo.value === "LCL") {
          if (grupoEmbalajeLCL) grupoEmbalajeLCL.classList.remove("d-none");
          if (embalajeLCL && embalajeLCL.value === "OTRO") {
            if (grupoOtroLCL) grupoOtroLCL.classList.remove("d-none");
          }
        }
      }
    } else if (valorModo === "TerrestreFerroviario") {
      labelTransporte.textContent = "Nombre Transporte Terrestre";
      if (grupoTerrestre) grupoTerrestre.classList.remove("d-none");
      if (tipoEmbalajeTerrestre && tipoEmbalajeTerrestre.value === "OTRO") {
        if (grupoOtroTerrestre) grupoOtroTerrestre.classList.remove("d-none");
      }
    } else {
      labelTransporte.textContent = "Nombre Transporte";
    }
  }

  function actualizarVistaTransporte() {
    const modo = (modoTransporte && modoTransporte.value) || "";
    const labelNombreTransporte   = document.getElementById("label_nombre_transporte");
    const labelNumeroViaje        = document.getElementById("label_numero_viaje");
    const labelAeropuertoOrigen   = document.getElementById("label_aeropuerto_origen");
    const labelAeropuertoDestino  = document.getElementById("label_aeropuerto_destino");
    const grupoAeropuertoOrigen   = document.getElementById("grupo_aeropuerto_origen");
    const grupoAeropuertoDestino  = document.getElementById("grupo_aeropuerto_destino");

    if (modo === "Aereo") {
      if (labelNombreTransporte)  labelNombreTransporte.textContent  = "Nombre Avión / Línea Aérea";
      if (labelNumeroViaje)       labelNumeroViaje.textContent       = "N° Viaje / Vuelo";
      if (labelAeropuertoOrigen)  labelAeropuertoOrigen.textContent  = "Aeropuerto Origen";
      if (labelAeropuertoDestino) labelAeropuertoDestino.textContent = "Aeropuerto Destino";
      if (grupoAeropuertoOrigen)  grupoAeropuertoOrigen.classList.remove("d-none");
      if (grupoAeropuertoDestino) grupoAeropuertoDestino.classList.remove("d-none");
      if (vueloOrigenPais && vueloOrigenPais.value)   vueloOrigenPais.dispatchEvent(new Event("change"));
      if (vueloDestinoPais && vueloDestinoPais.value) vueloDestinoPais.dispatchEvent(new Event("change"));

    } else if (modo === "Maritimo") {
      if (labelNombreTransporte)  labelNombreTransporte.textContent  = "Nombre Buque / Naviera";
      if (labelNumeroViaje)       labelNumeroViaje.textContent       = "N° Viaje / Travesía";
      if (labelAeropuertoOrigen)  labelAeropuertoOrigen.textContent  = "Puerto de Origen";
      if (labelAeropuertoDestino) labelAeropuertoDestino.textContent = "Puerto de Destino";
      if (grupoAeropuertoOrigen)  grupoAeropuertoOrigen.classList.remove("d-none");
      if (grupoAeropuertoDestino) grupoAeropuertoDestino.classList.remove("d-none");
      if (vueloOrigenPais && vueloOrigenPais.value)   vueloOrigenPais.dispatchEvent(new Event("change"));
      if (vueloDestinoPais && vueloDestinoPais.value) vueloDestinoPais.dispatchEvent(new Event("change"));

    } else {
      if (labelNombreTransporte) labelNombreTransporte.textContent = "Nombre Transporte";
      if (labelNumeroViaje)      labelNumeroViaje.textContent      = "N° Viaje";
      const grupoAeropuertoOrigenEl  = document.getElementById("grupo_aeropuerto_origen");
      const grupoAeropuertoDestinoEl = document.getElementById("grupo_aeropuerto_destino");
      if (grupoAeropuertoOrigenEl)  grupoAeropuertoOrigenEl.classList.add("d-none");
      if (grupoAeropuertoDestinoEl) grupoAeropuertoDestinoEl.classList.add("d-none");
    }

    actualizarVistaEmbalaje();
  }

  // =====================
  // AUTOCOMPLETE (versión con #transporte-resultados)
  // =====================
  const inputTransporte         = document.getElementById('id_nombre_transporte');
  const resultadosTransporteDiv = document.getElementById('transporte-resultados');

  if (inputTransporte && resultadosTransporteDiv && modoTransporte) {
    inputTransporte.addEventListener('keyup', async (e) => {
      const query = e.target.value.trim();
      const modo  = modoTransporte.value;

      if (query.length < 2) {
        resultadosTransporteDiv.innerHTML = '';
        resultadosTransporteDiv.style.display = 'none';
        return;
      }

      let url = '';
      if (modo === 'Aereo')       url = `/buscar-aerolineas/?query=${encodeURIComponent(query)}`;
      else if (modo === 'Maritimo') url = `/buscar-navios/?query=${encodeURIComponent(query)}`;
      else {
        resultadosTransporteDiv.style.display = 'none';
        return;
      }

      try {
        const res  = await fetch(url);
        const data = await res.json();
        resultadosTransporteDiv.innerHTML = '';

        if (data.results && data.results.length > 0) {
          resultadosTransporteDiv.style.display = 'block';
          data.results.forEach(item => {
            const divItem = document.createElement('div');
            divItem.classList.add('autocomplete-item');

            let logoHtml = '';
            if (modo === 'Aereo' && item.iata) {
              logoHtml = `<img src="https://images.daisycon.io/airline/?iata=${item.iata}"
                               alt="${item.name}"
                               onerror="this.src='/static/img/avion-default.png'">`;
            } else if (modo === 'Maritimo') {
              logoHtml = `<img src="/static/img/barco.png" alt="Navío">`;
            }

            divItem.innerHTML = `${logoHtml}<span>${item.name}</span>`;
            divItem.addEventListener('click', () => {
              inputTransporte.value = item.name;
              resultadosTransporteDiv.innerHTML = '';
              resultadosTransporteDiv.style.display = 'none';
            });

            resultadosTransporteDiv.appendChild(divItem);
          });
        } else {
          resultadosTransporteDiv.style.display = 'none';
        }
      } catch (err) {
        console.error("Error en autocompletado:", err);
        resultadosTransporteDiv.style.display = 'none';
      }
    });

    document.addEventListener('click', (e) => {
      if (!resultadosTransporteDiv.contains(e.target) && e.target !== inputTransporte) {
        resultadosTransporteDiv.style.display = 'none';
      }
    });
  }

  // =====================
  // PRIMA & MONTOS
  // =====================
  const fcaInput            = document.getElementById("id_valor_fca");
  const fleteInput          = document.getElementById("id_valor_flete");
  const clienteSelect       = document.getElementById("id_cliente");
  const tipoCargaSelect     = document.getElementById("id_tipo_carga");
  const montoAseguradoInput = document.getElementById("montoAsegurado");
  const montoAseguradoHidden= document.getElementById("montoAseguradoHidden");
  const primaHiddenInput    = document.getElementById("id_valor_prima");
  const primaVisualInput    = document.getElementById("valorPrimaFormateado");
  const togglePrima         = document.getElementById("togglePrima");

  function calcularMontoAsegurado() {
    const fca   = parseFloat((fcaInput?.value || '').replace(',', '.'))   || 0;
    const flete = parseFloat((fleteInput?.value || '').replace(',', '.')) || 0;
    const asegurado = (fca + flete) * 1.10;

    if (montoAseguradoInput)  montoAseguradoInput.value  = asegurado.toFixed(2);
    if (montoAseguradoHidden) montoAseguradoHidden.value = asegurado.toFixed(2);

    // Solo si la prima NO está en modo manual
    if (togglePrima && !togglePrima.checked) {
      if (clienteSelect && clienteSelect.selectedIndex > 0 && tipoCargaSelect) {
        const selected  = clienteSelect.options[clienteSelect.selectedIndex];
        const tipoCarga = tipoCargaSelect.value;
        let tasa = 0.15, minimo = 20.0;

        if (tipoCarga === 'PolizaCongelada') {
          tasa   = parseFloat(selected.dataset.tasaCongelada);
          minimo = parseFloat(selected.dataset.minimoCongelado);
        } else {
          tasa   = parseFloat(selected.dataset.tasa);
          minimo = parseFloat(selected.dataset.minimo);
        }

        const primaCalculada = Math.max(asegurado * (tasa / 100), minimo);
        if (primaHiddenInput) primaHiddenInput.value = primaCalculada.toFixed(2);
        if (primaVisualInput) {
          primaVisualInput.value = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
                                    .format(primaCalculada);
        }
      }
    }
  }

  if (togglePrima && primaVisualInput && primaHiddenInput) {
    togglePrima.addEventListener("change", function () {
      if (this.checked) {
        // manual
        primaVisualInput.readOnly = false;
        primaVisualInput.value = primaHiddenInput.value;
        primaVisualInput.focus();
      } else {
        // automático
        primaVisualInput.readOnly = true;
        calcularMontoAsegurado();
      }
    });
    primaVisualInput.addEventListener("input", function () {
      let raw = this.value.replace(/[^0-9.,]/g, "").replace(",", ".");
      primaHiddenInput.value = (parseFloat(raw || "0") || 0).toFixed(2);
    });
  }

  [fcaInput, fleteInput, clienteSelect, tipoCargaSelect].forEach(el => {
    if (el) el.addEventListener("change", calcularMontoAsegurado);
  });

  // =====================
  // COPY HELPERS (producto -> viaje)
  // =====================
  function copiarValorSiVacio(origen, destino) {
    if (origen && destino && origen.value) {
      if (!destino.value || destino.value !== origen.value) {
        destino.value = origen.value;
        destino.dispatchEvent(new Event('change'));
      } else {
        destino.dispatchEvent(new Event('change'));
      }
    }
  }

  // =====================
  // INIT
  // =====================
  cargarPaises();
  calcularMontoAsegurado();
  actualizarVistaTransporte();

  if (modoTransporte) modoTransporte.addEventListener("change", actualizarVistaTransporte);
  if (tipoEmbalajeAereo)    tipoEmbalajeAereo.addEventListener("change", actualizarVistaEmbalaje);
  if (embalajeMaritimo)     embalajeMaritimo.addEventListener("change", actualizarVistaEmbalaje);
  if (embalajeLCL)          embalajeLCL.addEventListener("change", actualizarVistaEmbalaje);
  if (tipoEmbalajeTerrestre)tipoEmbalajeTerrestre.addEventListener("change", actualizarVistaEmbalaje);

  // Precarga de ruta -> viaje (si están vacíos)
  if (paisOrigenRuta && vueloOrigenPais)   copiarValorSiVacio(paisOrigenRuta,   vueloOrigenPais);
  if (ciudadOrigenRuta && vueloOrigenCiudad) copiarValorSiVacio(ciudadOrigenRuta, vueloOrigenCiudad);
  if (paisDestinoRuta && vueloDestinoPais) copiarValorSiVacio(paisDestinoRuta,  vueloDestinoPais);
  if (ciudadDestinoRuta && vueloDestinoCiudad) copiarValorSiVacio(ciudadDestinoRuta, vueloDestinoCiudad);

  // Sync dinámico
  if (paisOrigenRuta && vueloOrigenPais) {
    paisOrigenRuta.addEventListener('change', () => copiarValorSiVacio(paisOrigenRuta, vueloOrigenPais));
  }
  if (ciudadOrigenRuta && vueloOrigenCiudad) {
    ciudadOrigenRuta.addEventListener('change', () => copiarValorSiVacio(ciudadOrigenRuta, vueloOrigenCiudad));
  }
  if (paisDestinoRuta && vueloDestinoPais) {
    paisDestinoRuta.addEventListener('change', () => copiarValorSiVacio(paisDestinoRuta, vueloDestinoPais));
  }
  if (ciudadDestinoRuta && vueloDestinoCiudad) {
    ciudadDestinoRuta.addEventListener('change', () => copiarValorSiVacio(ciudadDestinoRuta, vueloDestinoCiudad));
  }
});
