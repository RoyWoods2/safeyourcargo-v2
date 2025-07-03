document.addEventListener("DOMContentLoaded", function () {
  const modoTransporte = document.getElementById("modoTransporte");

  // Variables para detalles de viaje y ruta (ya existentes en formulario_viaje.js)
  const vueloOrigenPais = document.getElementById("vueloOrigenPais");
  const vueloOrigenCiudad = document.getElementById("vueloOrigenCiudad");
  const vueloDestinoPais = document.getElementById("vueloDestinoPais");
  const vueloDestinoCiudad = document.getElementById("vueloDestinoCiudad");

  const selectAeropuertoOrigen = document.getElementById("id_aeropuerto_origen");
  const selectAeropuertoDestino = document.getElementById("id_aeropuerto_destino");

  const paisOrigenRuta = document.getElementById("paisOrigen");
  const ciudadOrigenRuta = document.getElementById("ciudadOrigen");
  const paisDestinoRuta = document.getElementById("paisDestino");
  const ciudadDestinoRuta = document.getElementById("ciudadDestino");

  const paisesMap = {}; // CL -> Chile

  // Nuevas variables para la lógica de embalaje y autocomplete
  const nombreTransporteInput = document.querySelector("input[name*='nombre_transporte']") ||
                               document.querySelector("input[name*='nombre_avion']") ||
                               document.getElementById("id_nombre_avion"); // Ajustado para ser más robusto sin {{ viaje_form.nombre_avion.id_for_label }}
  const labelTransporte = document.getElementById("label_nombre_transporte");

  // AÉREO
  const grupoAereo = document.getElementById("grupo_embalaje_aereo");
  const tipoEmbalajeAereo = document.getElementById("tipoEmbalajeAereo");
  const grupoOtroAereo = document.getElementById("grupo_otro_embalaje_aereo");
  // MARÍTIMO
  const grupoMaritimo = document.getElementById("grupo_embalaje_maritimo");
  const embalajeMaritimo = document.getElementById("embalajeMaritimo");
  const grupoTipoContenedor = document.getElementById("grupo_tipo_container_maritimo");
  const tipoContainer = document.getElementById("tipoContainerMaritimo");
  const grupoEmbalajeLCL = document.getElementById("grupo_tipo_embalaje_maritimo_lcl");
  const embalajeLCL = document.getElementById("tipoEmbalajeLCL");
  const grupoOtroLCL = document.getElementById("grupo_otro_embalaje_lcl");
  // TERRESTRE
  const grupoTerrestre = document.getElementById("grupo_embalaje_terrestre");
  const tipoEmbalajeTerrestre = document.getElementById("tipoEmbalajeTerrestre");
  const grupoOtroTerrestre = document.getElementById("grupo_otro_embalaje_terrestre");

  // Variables para autocomplete
  let autocompleteContainer = null;
  let currentResults = [];
  let selectedIndex = -1;
  let timeoutId = null;

  // 🔹 Cargar países y poblar todos los selects
  function cargarPaises() {
    fetch("/api/paises/")
      .then(response => response.json())
      .then(data => {
        if (data.paises) {
          data.paises.forEach(pais => {
            paisesMap[pais.codigo] = pais.nombre; // ✅ clave del fix

            const opt1 = new Option(pais.nombre, pais.codigo);
            const opt2 = new Option(pais.nombre, pais.codigo);
            if (vueloOrigenPais) vueloOrigenPais.appendChild(opt1);
            if (vueloDestinoPais) vueloDestinoPais.appendChild(opt2);

            const opt3 = new Option(pais.nombre, pais.codigo);
            const opt4 = new Option(pais.nombre, pais.codigo);
            if (paisOrigenRuta) paisOrigenRuta.appendChild(opt3);
            if (paisDestinoRuta) paisDestinoRuta.appendChild(opt4);
          });
        }
      })
      .catch(error => console.error("Error cargando países:", error));
  }

  // 🔹 Utilidad CSRF
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

  // 🔹 Cargar ciudades
  function cargarCiudades(nombrePais, select) {
    if (!nombrePais) return;
    select.innerHTML = '<option value="">Cargando ciudades...</option>';
    fetch("/api/ciudades/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken")
      },
      body: JSON.stringify({ pais: nombrePais })
    })
      .then(res => res.json())
      .then(data => {
        select.innerHTML = '<option value="">Seleccione una ciudad</option>';
        (data.ciudades || []).forEach(ciudad => {
          const option = new Option(ciudad, ciudad);
          select.appendChild(option);
        });
      })
      .catch(() => {
        select.innerHTML = '<option value="">Error al cargar</option>';
      });
  }

  // 🔹 Cargar aeropuertos
  function cargarAeropuertos(nombrePais, select) {
    if (!nombrePais) return;
    select.innerHTML = '<option value="">Cargando aeropuertos...</option>';
    fetch("/api/aeropuertos/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken")
      },
      body: JSON.stringify({ pais: nombrePais })
    })
      .then(res => res.json())
      .then(data => {
        select.innerHTML = '<option value="">Seleccione un aeropuerto</option>';
        (data.aeropuertos || []).forEach(a => {
          const option = new Option(`${a.name} (${a.city})`, a.iata);
          select.appendChild(option);
        });
      })
      .catch(() => {
        select.innerHTML = '<option value="">Error al cargar</option>';
      });
  }

  // 🔹 Cargar puertos marítimos
  function cargarPuertos(codigoPais, select) {
    if (!codigoPais) return;
    select.innerHTML = '<option value="">Cargando puertos...</option>';
    fetch("/api/unlocode/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken")
      },
      body: JSON.stringify({ pais: codigoPais, function: "1" })
    })
      .then(res => res.json())
      .then(data => {
        select.innerHTML = '<option value="">Seleccione un puerto</option>';
        (data.ubicaciones || []).forEach(p => {
          const option = new Option(`${p.name} (${p.locode})`, p.locode);
          select.appendChild(option);
        });
      })
      .catch(() => {
        select.innerHTML = '<option value="">Error al cargar</option>';
      });
  }

  // 🔹 Eventos para DETALLES DE VIAJE
  vueloOrigenPais.addEventListener("change", () => {
    const codigo = vueloOrigenPais.value;
    const nombre = paisesMap[codigo] || "";
    cargarCiudades(nombre, vueloOrigenCiudad);

    const modo = modoTransporte.value;
    if (modo === "Aereo") {
      cargarAeropuertos(nombre, selectAeropuertoOrigen);
    } else if (modo === "Maritimo") {
      cargarPuertos(codigo, selectAeropuertoOrigen);
    }
  });

  vueloDestinoPais.addEventListener("change", () => {
    const codigo = vueloDestinoPais.value;
    const nombre = paisesMap[codigo] || "";
    cargarCiudades(nombre, vueloDestinoCiudad);

    const modo = modoTransporte.value;
    if (modo === "Aereo") {
      cargarAeropuertos(nombre, selectAeropuertoDestino);
    } else if (modo === "Maritimo") {
      cargarPuertos(codigo, selectAeropuertoDestino);
    }
  });

  // 🔹 Eventos para RUTA
  if (paisOrigenRuta && ciudadOrigenRuta) {
    paisOrigenRuta.addEventListener("change", () => {
      const paisNombre = paisOrigenRuta.options[paisOrigenRuta.selectedIndex].textContent;
      cargarCiudades(paisNombre, ciudadOrigenRuta);
    });
  }

  if (paisDestinoRuta && ciudadDestinoRuta) {
    paisDestinoRuta.addEventListener("change", () => {
      const paisNombre = paisDestinoRuta.options[paisDestinoRuta.selectedIndex].textContent;
      cargarCiudades(paisNombre, ciudadDestinoRuta);
    });
  }

  // --- Lógica de VISTA DE EMBALAJE (movida del script HTML) ---
  function actualizarVistaEmbalaje() {
    const valorModo = modoTransporte.value;
    // Resetear todos los grupos a ocultos
    [grupoAereo, grupoOtroAereo, grupoMaritimo, grupoTipoContenedor,
     grupoEmbalajeLCL, grupoOtroLCL, grupoTerrestre, grupoOtroTerrestre].forEach(e => {
        if (e) e.classList.add("d-none");
    });
    
    // Actualizar label del campo de transporte y mostrar grupos relevantes
    if (labelTransporte) { // Asegurarse de que el label exista
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
            labelTransporte.textContent = "Nombre Transporte"; // Default
        }
    }
    
    // Limpiar autocomplete cuando cambia el modo
    cerrarAutocomplete();
  }

  // --- Funciones de Autocomplete (movidas del script HTML) ---
  function crearAutocomplete() {
    if (autocompleteContainer) return;
    
    autocompleteContainer = document.createElement('div');
    autocompleteContainer.className = 'autocomplete-container';
    autocompleteContainer.style.cssText = `
      position: absolute;
      top: 100%;
      left: 0;
      right: 0;
      background: white;
      border: 1px solid #ddd;
      border-top: none;
      max-height: 200px;
      overflow-y: auto;
      z-index: 1000;
      box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    `;
    
    if (nombreTransporteInput && nombreTransporteInput.parentNode) {
      nombreTransporteInput.parentNode.style.position = 'relative';
      nombreTransporteInput.parentNode.appendChild(autocompleteContainer);
    }
  }

  function mostrarResultados(results) {
    if (!autocompleteContainer) crearAutocomplete();
    if (!autocompleteContainer) return; // Salir si no se pudo crear

    currentResults = results;
    selectedIndex = -1;
    
    autocompleteContainer.innerHTML = '';
    
    if (results.length === 0) {
      autocompleteContainer.style.display = 'none';
      return;
    }
    
    results.forEach((result, index) => {
      const item = document.createElement('div');
      item.className = 'autocomplete-item';
      item.style.cssText = `
        padding: 10px;
        cursor: pointer;
        border-bottom: 1px solid #eee;
        transition: background-color 0.2s;
      `;
      item.textContent = result.name;
      
      item.addEventListener('mouseenter', () => {
        selectedIndex = index;
        actualizarSeleccion();
      });
      
      item.addEventListener('click', () => {
        seleccionarItem(result);
      });
      
      autocompleteContainer.appendChild(item);
    });
    
    autocompleteContainer.style.display = 'block';
  }

  function actualizarSeleccion() {
    if (!autocompleteContainer) return;
    const items = autocompleteContainer.querySelectorAll('.autocomplete-item');
    items.forEach((item, index) => {
      if (index === selectedIndex) {
        item.style.backgroundColor = '#007bff';
        item.style.color = 'white';
      } else {
        item.style.backgroundColor = 'transparent';
        item.style.color = 'black';
      }
    });
  }

  function seleccionarItem(result) {
    if (nombreTransporteInput) {
      nombreTransporteInput.value = result.name;
    }
    cerrarAutocomplete();
  }

  function cerrarAutocomplete() {
    if (autocompleteContainer) {
      autocompleteContainer.style.display = 'none';
    }
    selectedIndex = -1;
  }

  // Buscar transporte en API
  function buscarTransporte(query) {
    if (query.length < 2) {
      cerrarAutocomplete();
      return;
    }
    
    const tipoTransporte = modoTransporte.value.toLowerCase();
    
    // Solo buscar para aéreo y marítimo
    if (!['aereo', 'maritimo'].includes(tipoTransporte)) {
      cerrarAutocomplete();
      return;
    }
    
    const url = `/api/buscar-transporte/?tipo=${tipoTransporte}&q=${encodeURIComponent(query)}`;
    
    fetch(url)
      .then(response => response.json())
      .then(data => {
        if (data.results && data.results.length > 0) {
          mostrarResultados(data.results);
        } else {
          cerrarAutocomplete();
        }
      })
      .catch(error => {
        console.error('Error en búsqueda de transporte:', error);
        cerrarAutocomplete();
      });
  }

  // --- Lógica de actualizarVistaTransporte (la versión más robusta) ---
  function actualizarVistaTransporte() {
    const modo = modoTransporte.value;

    const labelNombreTransporte = document.getElementById("label_nombre_transporte");
    const labelNumeroViaje = document.getElementById("label_numero_viaje");
    const labelAeropuertoOrigen = document.getElementById("label_aeropuerto_origen");
    const labelAeropuertoDestino = document.getElementById("label_aeropuerto_destino");

    const grupoAeropuertoOrigen = document.getElementById("grupo_aeropuerto_origen");
    const grupoAeropuertoDestino = document.getElementById("grupo_aeropuerto_destino");

    if (modo === "Aereo") {
      if (labelNombreTransporte) labelNombreTransporte.textContent = "Nombre Avión / Línea Aérea";
      if (labelNumeroViaje) labelNumeroViaje.textContent = "N° Viaje / Vuelo";
      if (labelAeropuertoOrigen) labelAeropuertoOrigen.textContent = "Aeropuerto Origen";
      if (labelAeropuertoDestino) labelAeropuertoDestino.textContent = "Aeropuerto Destino";

      if (grupoAeropuertoOrigen) grupoAeropuertoOrigen.classList.remove("d-none");
      if (grupoAeropuertoDestino) grupoAeropuertoDestino.classList.remove("d-none");

      // Disparar eventos para recargar aeropuertos si el país ya está seleccionado
      if (vueloOrigenPais && vueloOrigenPais.value) {
        vueloOrigenPais.dispatchEvent(new Event('change'));
      }
      if (vueloDestinoPais && vueloDestinoPais.value) {
        vueloDestinoPais.dispatchEvent(new Event('change'));
      }

    } else if (modo === "Maritimo") {
      if (labelNombreTransporte) labelNombreTransporte.textContent = "Nombre Buque / Naviera";
      if (labelNumeroViaje) labelNumeroViaje.textContent = "N° Viaje / Travesía";
      if (labelAeropuertoOrigen) labelAeropuertoOrigen.textContent = "Puerto de Origen";
      if (labelAeropuertoDestino) labelAeropuertoDestino.textContent = "Puerto de Destino";

      if (grupoAeropuertoOrigen) grupoAeropuertoOrigen.classList.remove("d-none");
      if (grupoAeropuertoDestino) grupoAeropuertoDestino.classList.remove("d-none");

      // Disparar eventos para recargar puertos si el país ya está seleccionado
      if (vueloOrigenPais && vueloOrigenPais.value) {
        vueloOrigenPais.dispatchEvent(new Event('change'));
      }
      if (vueloDestinoPais && vueloDestinoPais.value) {
        vueloDestinoPais.dispatchEvent(new Event('change'));
      }

    } else if (modo === "TerrestreFerroviario") {
      if (labelNombreTransporte) labelNombreTransporte.textContent = "Nombre Vehículo / Línea Ferroviaria";
      if (labelNumeroViaje) labelNumeroViaje.textContent = "N° Viaje / Transporte";

      // Ocultar completamente los contenedores de los "aeropuertos"
      if (grupoAeropuertoOrigen) grupoAeropuertoOrigen.classList.add("d-none");
      if (grupoAeropuertoDestino) grupoAeropuertoDestino.classList.add("d-none");

    } else {
      // Otros casos o valor por defecto
      if (labelNombreTransporte) labelNombreTransporte.textContent = "Nombre Transporte";
      if (labelNumeroViaje) labelNumeroViaje.textContent = "N° Viaje";

      if (grupoAeropuertoOrigen) grupoAeropuertoOrigen.classList.add("d-none");
      if (grupoAeropuertoDestino) grupoAeropuertoDestino.classList.add("d-none");
    }

    // Llama a actualizarVistaEmbalaje después de actualizar la vista de transporte
    actualizarVistaEmbalaje();
  }

  // --- Función copiarValorSiVacio (movida del script HTML) ---
  function copiarValorSiVacio(origen, destino) {
    if (origen && destino && origen.value) {
      if (!destino.value || destino.value !== origen.value) {
        destino.value = origen.value;
        destino.dispatchEvent(new Event('change'));
      } else if (destino.value === origen.value) {
        destino.dispatchEvent(new Event('change'));
      }
    }
  }

  // 🔹 Ejecutar carga inicial y añadir listeners
  cargarPaises();
  actualizarVistaTransporte(); // Inicializa ambas vistas

  // Listeners para Modo de Transporte y Embalaje
  modoTransporte.addEventListener("change", actualizarVistaTransporte);
  if (tipoEmbalajeAereo) tipoEmbalajeAereo.addEventListener("change", actualizarVistaEmbalaje);
  if (embalajeMaritimo) embalajeMaritimo.addEventListener("change", actualizarVistaEmbalaje);
  if (embalajeLCL) embalajeLCL.addEventListener("change", actualizarVistaEmbalaje);
  if (tipoEmbalajeTerrestre) tipoEmbalajeTerrestre.addEventListener("change", actualizarVistaEmbalaje);

  // Autocomplete event listeners
  if (nombreTransporteInput) {
    nombreTransporteInput.addEventListener('input', function(e) {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        buscarTransporte(e.target.value);
      }, 300); // Debounce de 300ms
    });

    nombreTransporteInput.addEventListener('keydown', function(e) {
      if (!autocompleteContainer || autocompleteContainer.style.display === 'none') return;
      
      switch(e.key) {
        case 'ArrowDown':
          e.preventDefault();
          selectedIndex = Math.min(selectedIndex + 1, currentResults.length - 1);
          actualizarSeleccion();
          break;
        case 'ArrowUp':
          e.preventDefault();
          selectedIndex = Math.max(selectedIndex - 1, -1);
          actualizarSeleccion();
          break;
        case 'Enter':
          e.preventDefault();
          if (selectedIndex >= 0 && currentResults[selectedIndex]) {
            seleccionarItem(currentResults[selectedIndex]);
          }
          break;
        case 'Escape':
          cerrarAutocomplete();
          break;
      }
    });
  }

  // Cerrar autocomplete al hacer click fuera
  document.addEventListener('click', function(e) {
    if (nombreTransporteInput && !nombreTransporteInput.contains(e.target) && 
        (!autocompleteContainer || !autocompleteContainer.contains(e.target))) {
      cerrarAutocomplete();
    }
  });

  // Precargar campos del producto en los campos del viaje (solo si están vacíos)
  copiarValorSiVacio(paisOrigenRuta, vueloOrigenPais);
  copiarValorSiVacio(ciudadOrigenRuta, vueloOrigenCiudad);
  copiarValorSiVacio(paisDestinoRuta, vueloDestinoPais);
  copiarValorSiVacio(ciudadDestinoRuta, vueloDestinoCiudad);

  // Copiar dinámicamente al seleccionar país/ciudad de origen del producto
  if (paisOrigenRuta) paisOrigenRuta.addEventListener('change', function () {
    copiarValorSiVacio(this, vueloOrigenPais);
  });

  if (ciudadOrigenRuta) ciudadOrigenRuta.addEventListener('change', function () {
    copiarValorSiVacio(this, vueloOrigenCiudad);
  });

  if (paisDestinoRuta) paisDestinoRuta.addEventListener('change', function () {
    copiarValorSiVacio(this, vueloDestinoPais);
  });

  if (ciudadDestinoRuta) ciudadDestinoRuta.addEventListener('change', function () {
    copiarValorSiVacio(this, vueloDestinoCiudad);
  });
});