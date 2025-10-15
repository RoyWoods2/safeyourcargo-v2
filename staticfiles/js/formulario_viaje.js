document.addEventListener("DOMContentLoaded", function () {
  // =========================================
  // ELEMENTOS BASE
  // =========================================
  const modoTransporte = document.getElementById("modoTransporte");

  // Detalles de viaje
  const vueloOrigenPais = document.getElementById("vueloOrigenPais");
  const vueloOrigenCiudad = document.getElementById("vueloOrigenCiudad");
  const vueloDestinoPais = document.getElementById("vueloDestinoPais");
  const vueloDestinoCiudad = document.getElementById("vueloDestinoCiudad");

  // Selects "aeropuerto / puerto"
  const selectAeropuertoOrigen = document.getElementById("id_aeropuerto_origen");
  const selectAeropuertoDestino = document.getElementById("id_aeropuerto_destino");

  // Ruta (producto)
  const paisOrigenRuta = document.getElementById("paisOrigen");
  const ciudadOrigenRuta = document.getElementById("ciudadOrigen");
  const paisDestinoRuta = document.getElementById("paisDestino");
  const ciudadDestinoRuta = document.getElementById("ciudadDestino");

  // Mapa: ISO-2 -> Nombre
  const paisesMap = {};

  // Etiquetas dinámicas
  const labelTransporte = document.getElementById("label_nombre_transporte");

  // =========================================
  // GRUPOS DE EMBALAJE
  // =========================================
  // Aéreo
  const grupoAereo = document.getElementById("grupo_embalaje_aereo");
  const tipoEmbalajeAereo = document.getElementById("id_tipo_embalaje_aereo");
  const grupoOtroAereo = document.getElementById("grupo_otro_embalaje_aereo");

  // Marítimo
  const grupoMaritimo = document.getElementById("grupo_embalaje_maritimo");
  const embalajeMaritimo = document.getElementById("id_embalaje_maritimo");
  const grupoContMar = document.getElementById("grupo_tipo_container_maritimo");
  const selContMar = document.getElementById("id_tipo_container_maritimo");
  const grupoEmbalajeLCL = document.getElementById("grupo_tipo_embalaje_lcl");
  const embalajeLCL = document.getElementById("id_tipo_embalaje_lcl");
  const grupoOtroLCL = document.getElementById("grupo_otro_embalaje_lcl");

  // Terrestre/Ferroviario
  const grupoTerrestre = document.getElementById("grupo_embalaje_terrestre");
  const tipoEmbalajeTerrestre = document.getElementById("id_tipo_embalaje_terrestre");
  const grupoContTer = document.getElementById("grupo_tipo_container_terrestre");
  const selContTer = document.getElementById("id_tipo_container_maritimo");
  const grupoOtroTerrestre = document.getElementById("grupo_otro_embalaje_terrestre");

  // =========================================
  // UTILS
  // =========================================
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

  function show(el) {
    if (el) el.classList.remove('d-none');
  }

  function hide(el) {
    if (el) el.classList.add('d-none');
  }

  // =========================================
  // CARGA DE PAISES / CIUDADES / AEROPUERTOS / PUERTOS
  // =========================================
  function cargarPaises() {
    [vueloOrigenPais, vueloDestinoPais, paisOrigenRuta, paisDestinoRuta].forEach(sel => {
      if (sel) sel.innerHTML = '';
    });
    fetch("/api/paises/")
      .then(r => r.json())
      .then(data => {
        const lista = data.paises || [];
        lista.forEach(pais => {
          paisesMap[pais.codigo] = pais.nombre;
          const optO = new Option(pais.nombre, pais.codigo);
          const optD = new Option(pais.nombre, pais.codigo);
          const optRO = new Option(pais.nombre, pais.codigo);
          const optRD = new Option(pais.nombre, pais.codigo);
          if (vueloOrigenPais) vueloOrigenPais.appendChild(optO);
          if (vueloDestinoPais) vueloDestinoPais.appendChild(optD);
          if (paisOrigenRuta) paisOrigenRuta.appendChild(optRO);
          if (paisDestinoRuta) paisDestinoRuta.appendChild(optRD);
        });
      })
      .catch(err => console.error("Error cargando países:", err));
  }

  function cargarCiudades(nombrePais, select) {
    if (!nombrePais || !select) return;
    select.innerHTML = '<option value="">Cargando ciudades...</option>';
    fetch("/api/ciudades/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({
          pais: nombrePais
        })
      })
      .then(res => res.json())
      .then(data => {
        select.innerHTML = '<option value="">Seleccione una ciudad</option>';
        (data.ciudades || []).forEach(c => select.appendChild(new Option(c, c)));
      })
      .catch(() => {
        select.innerHTML = '<option value="">Error al cargar</option>';
      });
  }

  function cargarAeropuertos(codigoPais, select) {
    if (!codigoPais || !select) return;
    const nombrePais = paisesMap[codigoPais] || "";
    select.innerHTML = '<option value="">Cargando aeropuertos...</option>';
    fetch("/api/aeropuertos/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({
          pais: nombrePais,
          pais_code: codigoPais
        })
      })
      .then(res => res.json())
      .then(data => {
        select.innerHTML = '<option value="">Seleccione un aeropuerto</option>';
        (data.aeropuertos || []).forEach(a => {
          select.appendChild(new Option(`${a.name} (${a.city})`, a.iata));
        });
      })
      .catch(() => {
        select.innerHTML = '<option value="">Error al cargar</option>';
      });
  }

  function cargarPuertos(codigoPais, select) {
    if (!codigoPais || !select) return;
    select.innerHTML = '<option value="">Cargando puertos...</option>';
    fetch("/api/unlocode/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({
          pais: codigoPais,
          function: "1"
        })
      })
      .then(res => res.json())
      .then(data => {
        select.innerHTML = '<option value="">Seleccione un puerto</option>';
        (data.ubicaciones || []).forEach(p => {
          select.appendChild(new Option(`${p.name} (${p.locode})`, p.locode));
        });
      })
      .catch(() => {
        select.innerHTML = '<option value="">Error al cargar</option>';
      });
  }

  // =========================================
  // OPCIONES DE EMBALAJE
  // =========================================
  const MARITIMO_OPTS = [{
    value: 'FCL',
    label: 'FCL'
  }, {
    value: 'LCL',
    label: 'LCL'
  }, ];
  const TERRESTRE_OPTS = [{
    value: '',
    label: 'Seleccione una opción'
  }, {
    value: 'FLC',
    label: 'FLC (En camión)'
  }, {
    value: 'LCL',
    label: 'LCL (En camión)'
  }, {
    value: 'OTRO',
    label: 'Otro (especificar)'
  }, ];

  function setOptions(selectEl, options, withPlaceholder = false) {
    if (!selectEl) return;
    const cur = selectEl.value;
    selectEl.innerHTML = '';
    if (withPlaceholder) selectEl.appendChild(new Option('Seleccione una opción', ''));
    options.forEach(o => selectEl.appendChild(new Option(o.label, o.value)));
    if ([...selectEl.options].some(o => o.value === cur)) selectEl.value = cur;
    selectEl.dispatchEvent(new Event('change'));
  }

  function ensureOptions(selectEl, desired, withPlaceholder = false) {
    if (!selectEl) return;
    const curr = Array.from(selectEl.options).map(o => o.value);
    const need = desired.map(o => o.value);
    const same = curr.length === need.length && need.every(v => curr.includes(v));
    if (!same) setOptions(selectEl, desired, withPlaceholder);
  }

  // =========================================
  // VISTA DE EMBALAJE + ETIQUETAS
  // =========================================
  function hideAllPacking() {
    [grupoAereo, grupoOtroAereo,
      grupoMaritimo, grupoContMar, grupoEmbalajeLCL, grupoOtroLCL,
      grupoTerrestre, grupoOtroTerrestre, grupoContTer
    ].forEach(hide);
  }

// Helpers
function show(el){ if(el) el.classList.remove('d-none'); }
function hide(el){ if(el) el.classList.add('d-none'); }
function clearSelect(sel){
  if(!sel) return;
  sel.value = '';
  sel.dispatchEvent(new Event('change'));
}

function actualizarVistaEmbalaje() {
  const modo = (modoTransporte && modoTransporte.value) || "";

  // Oculta todo
  [grupoAereo, grupoOtroAereo,
   grupoMaritimo, grupoContMar, grupoEmbalajeLCL, grupoOtroLCL,
   grupoTerrestre, grupoContTer, grupoOtroTerrestre
  ].forEach(hide);

  if (!labelTransporte) return;

  if (modo === "Aereo") {
    labelTransporte.textContent = "Nombre Avión / Línea Aérea";
    show(grupoAereo);
    if (tipoEmbalajeAereo && tipoEmbalajeAereo.value === "OTRO") show(grupoOtroAereo);
    return;
  }

  if (modo === "Maritimo" || modo === "MarRojo") {
    labelTransporte.textContent = "Nombre Navío / Línea Naviera";
    show(grupoMaritimo);

    const val = embalajeMaritimo ? embalajeMaritimo.value : "";
    if (val === "FCL") {
      // Requiere contenedor
      if (selContMar) selContMar.required = true;
      show(grupoContMar);
      hide(grupoEmbalajeLCL);
      hide(grupoOtroLCL);
      // Limpia posibles residuos LCL
      if (embalajeLCL) { embalajeLCL.value = ''; }
      const otroLcl = document.getElementById('id_otro_embalaje_lcl');
      if (otroLcl) otroLcl.value = '';
    } else if (val === "LCL") {
      // No requiere contenedor
      if (selContMar) selContMar.required = false;
      clearSelect(selContMar);
      hide(grupoContMar);
      show(grupoEmbalajeLCL);
      if (embalajeLCL && embalajeLCL.value === "OTRO") show(grupoOtroLCL);
    } else {
      // Nada seleccionado aún: limpia y oculta
      if (selContMar) selContMar.required = false;
      clearSelect(selContMar);
      hide(grupoContMar);
      hide(grupoEmbalajeLCL);
      hide(grupoOtroLCL);
    }
    return;
  }

  if (modo === "TerrestreFerroviario") {
    labelTransporte.textContent = "Nombre Transporte Terrestre";
    show(grupoTerrestre);

    const val = tipoEmbalajeTerrestre ? tipoEmbalajeTerrestre.value : "";
    if (val === "FLC") {
      if (selContTer) selContTer.required = true;  // reutiliza el mismo select del contenedor
      show(grupoContTer);
      hide(grupoEmbalajeLCL);
      hide(grupoOtroTerrestre);
      // Limpia posibles residuos LCL
      if (embalajeLCL) embalajeLCL.value = '';
      const otroLcl = document.getElementById('id_otro_embalaje_lcl');
      if (otroLcl) otroLcl.value = '';
    } else if (val === "LCL") {
      if (selContTer) selContTer.required = false;
      clearSelect(selContTer);
      hide(grupoContTer);
      show(grupoEmbalajeLCL);
      hide(grupoOtroTerrestre);
      if (embalajeLCL && embalajeLCL.value === "OTRO") show(grupoOtroLCL);
    } else if (val === "OTRO") {
      if (selContTer) selContTer.required = false;
      clearSelect(selContTer);
      hide(grupoEmbalajeLCL);
      show(grupoOtroTerrestre);
    } else {
      if (selContTer) selContTer.required = false;
      clearSelect(selContTer);
      hide(grupoEmbalajeLCL);
      hide(grupoOtroTerrestre);
    }
    return;
  }

  // Otro modo
  labelTransporte.textContent = "Nombre Transporte";
}

  function actualizarVistaTransporte() {
    const modo = (modoTransporte && modoTransporte.value) || "";
    const labelNombreTransporte = document.getElementById("label_nombre_transporte");
    const labelNumeroViaje = document.getElementById("label_numero_viaje");
    const grupoAeropuertoOrigen = document.getElementById("grupo_aeropuerto_origen");
    const grupoAeropuertoDestino = document.getElementById("grupo_aeropuerto_destino");
    const labelPuntoOrigen = document.getElementById("label_punto_origen");
    const labelPuntoDestino = document.getElementById("label_punto_destino");

    if (modo === "Aereo") {
      if (labelNombreTransporte) labelNombreTransporte.textContent = "Nombre Avión / Línea Aérea";
      if (labelNumeroViaje) labelNumeroViaje.textContent = "N° Viaje / Vuelo";
      if (labelPuntoOrigen) labelPuntoOrigen.textContent = "Aeropuerto Origen";
      if (labelPuntoDestino) labelPuntoDestino.textContent = "Aeropuerto Destino";
      if (grupoAeropuertoOrigen) show(grupoAeropuertoOrigen);
      if (grupoAeropuertoDestino) show(grupoAeropuertoDestino);
      if (vueloOrigenPais && vueloOrigenPais.value) vueloOrigenPais.dispatchEvent(new Event("change"));
      if (vueloDestinoPais && vueloDestinoPais.value) vueloDestinoPais.dispatchEvent(new Event("change"));
    } else if (modo === "Maritimo" || modo === "MarRojo") {
      if (labelNombreTransporte) labelNombreTransporte.textContent = "Nombre Buque / Naviera";
      if (labelNumeroViaje) labelNumeroViaje.textContent = "N° Viaje / Travesía";
      if (labelPuntoOrigen) labelPuntoOrigen.textContent = "Puerto de Origen";
      if (labelPuntoDestino) labelPuntoDestino.textContent = "Puerto de Destino";
      if (grupoAeropuertoOrigen) show(grupoAeropuertoOrigen);
      if (grupoAeropuertoDestino) show(grupoAeropuertoDestino);
      if (vueloOrigenPais && vueloOrigenPais.value) vueloOrigenPais.dispatchEvent(new Event("change"));
      if (vueloDestinoPais && vueloDestinoPais.value) vueloDestinoPais.dispatchEvent(new Event("change"));
    } else {
      if (labelNombreTransporte) labelNombreTransporte.textContent = "Nombre Transporte";
      if (labelNumeroViaje) labelNumeroViaje.textContent = "N° Viaje";
      if (grupoAeropuertoOrigen) hide(grupoAeropuertoOrigen);
      if (grupoAeropuertoDestino) hide(grupoAeropuertoDestino);
    }

    actualizarVistaEmbalaje();
  }

  // =========================================
  // EVENTOS: DETALLES DE VIAJE
  // =========================================
  if (vueloOrigenPais) {
    vueloOrigenPais.addEventListener("change", () => {
      const codigo = vueloOrigenPais.value;
      const nombre = paisesMap[codigo] || "";
      if (vueloOrigenCiudad) cargarCiudades(nombre, vueloOrigenCiudad);
      const modo = (modoTransporte && modoTransporte.value) || "";
      if (modo === "Aereo") cargarAeropuertos(codigo, selectAeropuertoOrigen);
      else if (modo === "Maritimo" || modo === "MarRojo") cargarPuertos(codigo, selectAeropuertoOrigen);
      else if (selectAeropuertoOrigen) selectAeropuertoOrigen.innerHTML = '<option value="">Seleccione una opción</option>';
    });
  }

  if (vueloDestinoPais) {
    vueloDestinoPais.addEventListener("change", () => {
      const codigo = vueloDestinoPais.value;
      const nombre = paisesMap[codigo] || "";
      if (vueloDestinoCiudad) cargarCiudades(nombre, vueloDestinoCiudad);
      const modo = (modoTransporte && modoTransporte.value) || "";
      if (modo === "Aereo") cargarAeropuertos(codigo, selectAeropuertoDestino);
      else if (modo === "Maritimo" || modo === "MarRojo") cargarPuertos(codigo, selectAeropuertoDestino);
      else if (selectAeropuertoDestino) selectAeropuertoDestino.innerHTML = '<option value="">Seleccione una opción</option>';
    });
  }

  // =========================================
  // EVENTOS: RUTA -> CIUDADES
  // =========================================
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

  // =========================================
  // AUTOCOMPLETE transporte (igual que antes)
  // =========================================
  const inputTransporte = document.getElementById('id_nombre_transporte');
  const resultadosTransporteDiv = document.getElementById('transporte-resultados');

  if (inputTransporte && resultadosTransporteDiv && modoTransporte) {
    inputTransporte.addEventListener('keyup', async (e) => {
      const query = e.target.value.trim();
      const modo = modoTransporte.value;
      if (query.length < 2) {
        resultadosTransporteDiv.innerHTML = '';
        resultadosTransporteDiv.style.display = 'none';
        return;
      }
      let url = '';
      if (modo === 'Aereo') url = `/buscar-aerolineas/?query=${encodeURIComponent(query)}`;
      else if (modo === 'Maritimo' || modo === 'MarRojo') url = `/buscar-navios/?query=${encodeURIComponent(query)}`;
      else {
        resultadosTransporteDiv.style.display = 'none';
        return;
      }
      try {
        const res = await fetch(url);
        const data = await res.json();
        resultadosTransporteDiv.innerHTML = '';
        if (data.results && data.results.length > 0) {
          resultadosTransporteDiv.style.display = 'block';
          data.results.forEach(item => {
            const divItem = document.createElement('div');
            divItem.classList.add('autocomplete-item');
            let logoHtml = '';
            if (modo === 'Aereo' && item.iata) {
              logoHtml = `<img src="https://images.daisycon.io/airline/?iata=${item.iata}" alt="${item.name}" onerror="this.src='/static/img/avion-default.png'">`;
            } else if (modo === 'Maritimo' || modo === 'MarRojo') {
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

  // =========================================
  // PRIMA & MONTOS (igual que antes)
  // =========================================
  const fcaInput = document.getElementById("id_valor_fca");
  const fleteInput = document.getElementById("id_valor_flete");
  const clienteSelect = document.getElementById("id_cliente");
  const tipoCargaSelect = document.getElementById("id_tipo_carga");
  const montoAseguradoInput = document.getElementById("montoAsegurado");
  const montoAseguradoHidden = document.getElementById("montoAseguradoHidden");
  const primaHiddenInput = document.getElementById("id_valor_prima");
  const primaVisualInput = document.getElementById("valorPrimaFormateado");
  const togglePrima = document.getElementById("togglePrima");

  function calcularMontoAsegurado() {
    const fca = parseFloat((fcaInput?.value || '').replace(',', '.')) || 0;
    const flete = parseFloat((fleteInput?.value || '').replace(',', '.')) || 0;
    const asegurado = (fca + flete) * 1.10;
    if (montoAseguradoInput) montoAseguradoInput.value = asegurado.toFixed(2);
    if (montoAseguradoHidden) montoAseguradoHidden.value = asegurado.toFixed(2);
    if (togglePrima && !togglePrima.checked) {
      if (clienteSelect && clienteSelect.selectedIndex > 0 && tipoCargaSelect) {
        const selected = clienteSelect.options[clienteSelect.selectedIndex];
        const tipoCarga = tipoCargaSelect.value;
        let tasa = 0.15,
          minimo = 20.0;
        if (tipoCarga === 'PolizaCongelada') {
          tasa = parseFloat(selected.dataset.tasaCongelada);
          minimo = parseFloat(selected.dataset.minimoCongelado);
        } else {
          tasa = parseFloat(selected.dataset.tasa);
          minimo = parseFloat(selected.dataset.minimo);
        }
        const primaCalculada = Math.max(asegurado * (tasa / 100), minimo);
        if (primaHiddenInput) primaHiddenInput.value = primaCalculada.toFixed(2);
        if (primaVisualInput) {
          primaVisualInput.value = new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
          }).format(primaCalculada);
        }
      }
    }
  }

  if (togglePrima && primaVisualInput && primaHiddenInput) {
    togglePrima.addEventListener("change", function () {
      if (this.checked) {
        primaVisualInput.readOnly = false;
        primaVisualInput.value = primaHiddenInput.value;
        primaVisualInput.focus();
      } else {
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

  // =========================================
  // COPY HELPERS (producto -> viaje)
  // =========================================
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

  function precargarRutaEnViaje() {
    if (paisOrigenRuta && vueloOrigenPais) copiarValorSiVacio(paisOrigenRuta, vueloOrigenPais);
    if (ciudadOrigenRuta && vueloOrigenCiudad) copiarValorSiVacio(ciudadOrigenRuta, vueloOrigenCiudad);
    if (paisDestinoRuta && vueloDestinoPais) copiarValorSiVacio(paisDestinoRuta, vueloDestinoPais);
    if (ciudadDestinoRuta && vueloDestinoCiudad) copiarValorSiVacio(ciudadDestinoRuta, vueloDestinoCiudad);
    if (paisOrigenRuta && vueloOrigenPais) paisOrigenRuta.addEventListener('change', () => copiarValorSiVacio(paisOrigenRuta, vueloOrigenPais));
    if (ciudadOrigenRuta && vueloOrigenCiudad) ciudadOrigenRuta.addEventListener('change', () => copiarValorSiVacio(ciudadOrigenRuta, vueloOrigenCiudad));
    if (paisDestinoRuta && vueloDestinoPais) paisDestinoRuta.addEventListener('change', () => copiarValorSiVacio(paisDestinoRuta, vueloDestinoPais));
    if (ciudadDestinoRuta && vueloDestinoCiudad) ciudadDestinoRuta.addEventListener('change', () => copiarValorSiVacio(ciudadDestinoRuta, vueloDestinoCiudad));
  }

  // =========================================
  // ENVÍO DE FORMULARIO CON SWEETALERT2
  // =========================================
  const formCertificado = document.getElementById("form-certificado");
  const spinnerOverlay = document.getElementById("spinner-overlay");
  
  if (formCertificado) {
    formCertificado.addEventListener("submit", async function (event) {
      event.preventDefault(); // Evita el envío por defecto del formulario

      // Elimina las clases de error y los mensajes de feedback anteriores
      document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
      document.querySelectorAll('.invalid-feedback').forEach(el => el.remove());

      // Muestra el spinner
      spinnerOverlay.style.display = 'flex';

      try {
        const formData = new FormData(formCertificado);
        
        const response = await fetch(formCertificado.action, {
          method: 'POST',
          body: formData,
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken'),
          }
        });

        const data = await response.json();

        if (response.ok) {
          Swal.fire({
            title: '¡Éxito!',
            text: 'Certificado creado correctamente.',
            icon: 'success',
            confirmButtonText: 'Ok'
          }).then(() => {
            // Recarga la página después de que el usuario haga clic en 'Ok'
            location.reload();
          });
        } else {
          // Manejar errores de validación
          let errorHtml = '<ul style="text-align: left; list-style-position: inside;">';
          const errors = data.errors;

          // Parsea y recorre los errores de manera segura
          let parsedErrors = {};
          if (typeof errors === 'string') {
              try {
                  parsedErrors = JSON.parse(errors);
              } catch (e) {
                  console.error("No se pudo parsear el JSON de errores:", e);
                  parsedErrors = { '__all__': ['Error en el servidor.'] };
              }
          } else {
              parsedErrors = errors;
          }

          for (const formName in parsedErrors) {
            const formErrors = parsedErrors[formName];

            // Si es un error general del formulario
            if (formName === '__all__') {
                formErrors.forEach(errorText => {
                    errorHtml += `<li><strong>Error general:</strong> ${errorText}</li>`;
                });
            } else {
                for (const fieldName in formErrors) {
                    const fieldErrors = formErrors[fieldName];
                    fieldErrors.forEach(errorText => {
                        // Resaltar el campo con error y añadir feedback
                        const fieldId = `id_${fieldName}`;
                        const fieldElement = document.getElementById(fieldId);
                        if (fieldElement) {
                            fieldElement.classList.add('is-invalid');
                            let feedback = fieldElement.parentElement.querySelector('.invalid-feedback');
                            if (!feedback) {
                                feedback = document.createElement('div');
                                feedback.classList.add('invalid-feedback');
                                fieldElement.parentElement.appendChild(feedback);
                            }
                            feedback.textContent = errorText;
                        }
                        // Agregar el error a la lista del SweetAlert
                        errorHtml += `<li><strong>${fieldName}:</strong> ${errorText}</li>`;
                    });
                }
            }
          }
          errorHtml += '</ul>';
          
          Swal.fire({
            title: 'Error de validación',
            html: 'Se encontraron los siguientes errores:<br>' + errorHtml,
            icon: 'error',
            confirmButtonText: 'Cerrar'
          });
        }
      } catch (error) {
        Swal.fire({
          title: 'Error de conexión',
          text: 'Ocurrió un error al intentar enviar el formulario. Inténtalo de nuevo.',
          icon: 'error',
          confirmButtonText: 'Cerrar'
        });
      } finally {
        spinnerOverlay.style.display = 'none';
      }
    });
  }

  // =========================================
  // INIT + EVENTOS
  // =========================================
  cargarPaises();
  calcularMontoAsegurado();
  precargarRutaEnViaje();
  actualizarVistaTransporte();
  if (modoTransporte) modoTransporte.addEventListener("change", actualizarVistaTransporte);
  if (tipoEmbalajeAereo) tipoEmbalajeAereo.addEventListener("change", actualizarVistaEmbalaje);
  if (embalajeMaritimo) embalajeMaritimo.addEventListener("change", actualizarVistaEmbalaje);
  if (embalajeLCL) embalajeLCL.addEventListener("change", actualizarVistaEmbalaje);
  if (tipoEmbalajeTerrestre) tipoEmbalajeTerrestre.addEventListener("change", actualizarVistaEmbalaje);
});