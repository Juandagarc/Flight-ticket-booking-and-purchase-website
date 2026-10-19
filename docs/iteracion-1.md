# Iteración 1 · Usuarios y oferta de vuelos

Alcance según el plan de iteraciones del documento de historias de usuario (02/10/2026): **HU-001 a HU-009**.
Cada historia se construyó en la API y en la web, y cada criterio de aceptación tiene al menos una prueba
automática. El último criterio de todas las historias, la confirmación del Product Owner, queda pendiente de la
revisión con el cliente.

## Resultado de las pruebas

| Suite | Herramienta | Pruebas | Resultado |
| --- | --- | --- | --- |
| API (`apps/api/tests`) | pytest contra PostgreSQL 16 | 105 | ✅ todas pasan |
| Web, unitarias (`apps/web/tests/unit`) | Vitest + Testing Library | 32 | ✅ todas pasan |
| Extremo a extremo (`apps/web/tests/e2e`) | Playwright (Chromium) | 11 escenarios | ✅ todos pasan |
| Calidad | ruff, ESLint, `tsc --noEmit`, `next build` | — | ✅ sin errores |
| Contenedores | `docker build` de la API y la web, `docker compose up` | — | ✅ arranca y responde |

## Trazabilidad: criterio de aceptación → prueba

### HU-001 · Registro de cliente (CU-01, pantalla 05)

| Criterio | Pruebas |
| --- | --- |
| No se crea la cuenta si falta un dato obligatorio o si el documento no es alfanumérico; indica qué corregir | `test_hu001_registro.py`: `test_falta_dato_obligatorio_…` (los 11 campos), `test_dato_obligatorio_en_blanco…`, `test_documento_no_alfanumerico_se_rechaza` · e2e «HU-001» (mensaje bajo el campo y los demás datos se conservan) |
| Documento ya registrado: informa que la cuenta existe y ofrece iniciar sesión | `test_documento_registrado_informa_que_la_cuenta_existe` · e2e «HU-001» (enlace «Ir a iniciar sesión») |
| Usuario en uso: pide otro | `test_usuario_en_uso_pide_otro` |
| Después del registro el cliente inicia sesión | `test_despues_del_registro_el_cliente_inicia_sesion` · e2e «HU-001» |
| Se crea con rol cliente y su monedero (RF-28, RF-30, RF-61) | `test_registro_crea_cliente_con_monedero_y_carrito` |

### HU-002 · Inicio de sesión (CU-02, pantalla 35)

| Criterio | Pruebas |
| --- | --- |
| Cliente llega a su dashboard; administrador y root al panel | `test_hu002_…`: tokens por rol · `rutas.test.ts` · e2e (root y admin → `/admin`, cliente → `/cliente`) |
| Credenciales inválidas: error y no inicia sesión | `test_credenciales_invalidas_…`, `test_cuenta_inactiva_…` · e2e «HU-002» |
| Root o administrador no puede reservar ni comprar | `test_root_y_administrador_no_pueden_reservar_ni_comprar` · `rutas.test.ts` · e2e (root y admin redirigidos al intentar `/reservar`) |

### HU-003 · Gestión del perfil (CU-03, pantalla 36)

| Criterio | Pruebas |
| --- | --- |
| Los cambios válidos quedan guardados y se ven al volver a ingresar | `test_cambios_validos_quedan_guardados_…` · e2e «HU-003» (cierra sesión y vuelve) |
| No se guarda si un dato obligatorio queda en blanco | `test_no_se_guarda_si_un_dato_obligatorio_…` · e2e «HU-003» |
| Completar el perfil no habilita compras al administrador | `test_completar_perfil_no_habilita_compras_…` · e2e «HU-002 y HU-003» |
| El documento no se edita (observación) | `test_el_documento_no_se_edita` · e2e (campo deshabilitado) |

### HU-004 · Cambio de contraseña (CU-04, pantalla 36)

| Criterio | Pruebas |
| --- | --- |
| Contraseña actual incorrecta: se rechaza | `test_contrasena_actual_incorrecta_se_rechaza` · e2e «HU-004» |
| Nueva y confirmación distintas: se indica | `test_confirmacion_distinta_se_indica` · e2e «HU-004» |
| Después del cambio solo la nueva permite ingresar (cliente, administrador y root) | `test_despues_del_cambio_solo_la_nueva_…` (los 3 roles) · e2e «HU-004» |

### HU-005 · Creación de administradores (CU-05, pantalla 38)

| Criterio | Pruebas |
| --- | --- |
| Solo una sesión de root ve y usa la opción | `test_solo_el_root_ve_y_usa_la_opcion` · `rutas.test.ts` · e2e «HU-005» |
| No se crea un administrador con un usuario existente | `test_no_se_crea_administrador_con_usuario_existente` · e2e «HU-005» |
| El administrador creado gestiona vuelos pero no compra ni reserva | `test_administrador_creado_gestiona_vuelos_pero_no_compra` · e2e «HU-006» y «HU-002 y HU-003» |

### HU-006 · Programación de vuelos (CU-06, CU-07, CU-16, CU-17, pantallas 26 y 27)

| Criterio | Pruebas |
| --- | --- |
| Código de dos letras y consecutivo, no editable | `test_codigo_con_dos_letras_y_consecutivo`, `test_el_codigo_no_se_puede_digitar_ni_editar` |
| Tiempo de vuelo y llegada en hora local del destino calculados | `test_tiempo_y_llegada_se_calculan_…`, `test_reglas_vuelos.py` (haversine, cambio de día, horario de verano en Madrid) · e2e «HU-006» |
| No se acepta origen o destino fuera del catálogo ni origen igual a destino | `test_no_acepta_rutas_fuera_del_catalogo` (6 casos) · `vuelo.test.tsx` (destinos que ofrece el formulario) · e2e «HU-006» |
| Al guardar aparece en Noticias y los suscriptores reciben el aviso | `test_al_guardar_aparece_en_noticias`, `test_al_guardar_los_suscriptores_reciben_el_aviso`, `test_un_fallo_de_correo_no_impide_programar` |

### HU-007 · Edición de vuelos (CU-08, pantalla 28)

| Criterio | Pruebas |
| --- | --- |
| Vuelo ya ocurrido o con tiquetes vendidos no se edita | `test_vuelo_con_tiquetes_vendidos_no_se_edita`, `test_vuelo_que_ya_ocurrio_no_se_edita`, `test_vuelo_cancelado_no_se_edita`, `test_tiquetes_de_reservas_canceladas_no_bloquean` |
| Cambiar origen, destino u hora recalcula tiempo y llegada | `test_cambiar_ruta_u_hora_recalcula_…`, `test_editar_solo_tarifas_conserva_horario` · e2e «HU-007» |
| Los cambios se ven en la búsqueda | `test_cambios_guardados_se_ven_en_la_busqueda_y_noticias` · e2e «HU-008» (busca la ruta editada) |

### HU-008 · Búsqueda de vuelos (CU-20, CU-21, pantallas 02 y 03)

| Criterio | Pruebas |
| --- | --- |
| Con origen, destino, fecha y pasajeros lista los vuelos que cumplen | `test_busqueda_principal_…` · e2e «HU-008» |
| Cada filtro funciona solo o combinado | `test_cada_filtro_funciona_solo`, `test_filtros_combinados`, `test_solo_vuelos_programados_y_futuros`, `test_validacion_de_rangos_y_pasajeros` |
| Un visitante que intenta reservar va al registro o al inicio de sesión | `test_visitante_que_intenta_reservar_…` · `rutas.test.ts` · e2e «HU-008» |
| Las búsquedas de un cliente quedan registradas | `test_las_busquedas_del_cliente_quedan_en_su_actividad`, `test_busquedas_de_visitante_o_admin_no_se_registran` · e2e (aparecen en «Búsquedas recientes») |

### HU-009 · Consulta de noticias y promociones (CU-14, pantallas 06 y 01)

| Criterio | Pruebas |
| --- | --- |
| Un vuelo nuevo aparece en Noticias apenas se programa | `test_vuelo_nuevo_aparece_en_noticias_apenas_se_programa` · e2e «HU-009» |
| Una promoción aparece con su precio unitario | `test_promocion_aparece_con_su_precio_unitario` |
| No se necesita iniciar sesión | `test_no_se_necesita_iniciar_sesion` · e2e «HU-009» (sin sesión, incluida la imagen en el inicio) |

## Decisiones de implementación

Detalles que los documentos no fijan y que el equipo decide (como indicó el docente). Conviene presentarlos al
cliente en la revisión:

| Tema | Decisión | Referencia |
| --- | --- | --- |
| Tiempo de vuelo | Distancia ortodrómica (haversine) entre coordenadas de la ciudad ÷ 800 km/h, al minuto superior. Configurable con `VELOCIDAD_PROMEDIO_KMH`. No suma tiempo de rodaje, así que los trayectos cortos salen breves (Bogotá–Cartagena ≈ 49 min). | RF-53 |
| Fecha y hora de salida | El administrador las digita en hora local de la ciudad de origen; la llegada se guarda en hora local del destino. | RF-02 |
| Código de vuelo | `FL` + consecutivo de 4 dígitos (FL0001…) con una secuencia de PostgreSQL. | RF-54 |
| Códigos de ciudad | IATA del aeropuerto o de la ciudad; Tunja, sin aeropuerto comercial, usa TUN; Mocoa usa VGZ. | RF-49 |
| Salida en el pasado | No se permite programar ni mover un vuelo a una fecha pasada. | RF-08 |
| Quién programa vuelos | Solo el rol administrador. El root crea administradores y cambia su contraseña. | RF-07, RF-31 |
| «Tiquetes vendidos» para editar | Cuentan los tiquetes de reservas vigentes y pagadas, porque una reserva bloquea sillas igual que una compra. | RF-08, RF-55 |
| Precio de la noticia | La tarifa más baja del vuelo (normalmente la económica), mostrado como «Desde». | RF-65 |
| Imagen alusiva | Si el administrador no da una URL, se usa una ilustración SVG del destino que genera la web (`/destinos/MAD.svg`). | RF-10, RF-65 |
| Búsqueda por precio | Un vuelo cumple el rango si alguna de sus dos tarifas cae en él. Pasajeros de 1 a 5 (tope de RF-15). Resultados ordenados por salida. | RF-68, RF-69 |
| Registro | Crea el usuario, el perfil, el monedero y el carrito en una transacción. Contraseña sin reglas de formato (no se exigieron). | RF-28, RF-30, RF-62 |
| Correo | SMTP configurable; sin `SMTP_HOST` los correos se escriben en el log. Un fallo de correo no impide programar el vuelo y queda la notificación como no enviada. | RNF-03 |
| Barrera de compra | La ruta `/reservar/{código}` y el endpoint `GET /reservas/acceso` aplican RF-33 y RF-34 desde ya; el flujo de reserva y compra llega en la iteración 2. | RF-33, RF-34 |

## Pendiente para la revisión con el cliente

- Confirmación del Product Owner de las 9 historias.
- Preguntas abiertas que afectan esta iteración: P-06 (vuelo de regreso desde un destino internacional: hoy no se
  puede programar Madrid–Bogotá porque Madrid no es origen permitido), P-44 y P-45 (uno o varios root; si el root edita
  o elimina administradores), P-47 (verificación del correo al registrarse) y P-50 (política de contraseñas).
- La suscripción a noticias es de la iteración 4 (HU-029). El aviso a suscriptores de HU-006 ya está implementado y
  probado con suscripciones creadas directamente en la base.

## Endpoints de la API

| Método | Ruta | Rol | HU |
| --- | --- | --- | --- |
| POST | `/auth/registro` | público | 001 |
| POST | `/auth/login` · GET `/auth/me` | público · sesión | 002 |
| GET · PUT · POST | `/usuarios/me/perfil` | cliente, administrador | 003 |
| PUT | `/usuarios/me/contrasena` | sesión | 004 |
| GET · POST | `/administradores` | root | 005 |
| GET | `/ciudades` | público | 006 |
| POST | `/vuelos` · GET `/vuelos/gestion` | administrador | 006 |
| PUT | `/vuelos/{codigo}` | administrador | 007 |
| GET | `/vuelos/buscar` · `/vuelos/{codigo}` | público (registra la búsqueda del cliente) | 008 |
| GET | `/usuarios/me/actividad` | cliente | 008 |
| GET | `/noticias` | público | 009 |
| GET | `/reservas/acceso` | cliente | 002, 008 |
