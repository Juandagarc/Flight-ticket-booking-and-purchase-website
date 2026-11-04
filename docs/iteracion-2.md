# Iteración 2 · Reserva, compra y monedero

Alcance según el plan de iteraciones del documento de historias de usuario: **HU-010 a HU-018**.
Cada historia está en la API y en la web, y cada criterio de aceptación tiene al menos una prueba
automática. La confirmación del Product Owner queda pendiente de la revisión con el cliente.

## Resultado de las pruebas

| Suite | Herramienta | Pruebas | Resultado |
| --- | --- | --- | --- |
| API (`apps/api/tests`) | pytest contra PostgreSQL 16 | 155 (50 nuevas) | todas pasan |
| Web, unitarias (`apps/web/tests/unit`) | Vitest | 34 | todas pasan |
| Extremo a extremo (`apps/web/tests/e2e`) | Playwright (Chromium) | 16 escenarios (5 nuevos) | todos pasan |
| Calidad | ruff, ESLint, `tsc --noEmit`, `next build` | — | sin errores |

## Reglas que se implementaron

- Solo un cliente reserva y compra. Root y administrador no pueden (RF-33, RF-34).
- Máximo 5 tiquetes por cliente en un mismo vuelo; los cancelados no cuentan.
- Un viajero no puede estar dos veces en el mismo vuelo.
- Un menor de edad debe viajar con al menos un adulto en la misma reserva.
- La silla se asigna al azar dentro de la clase elegida.
- Una reserva sin pagar se libera a las 24 horas, o antes si el vuelo sale primero. La liberación
  se revisa cada minuto y también antes de cada consulta de vuelos o reservas.
- El pago es solo con el saldo del monedero. Si no alcanza, no se descuenta nada ni se compra.
- Una compra se cancela hasta 1 hora antes del vuelo (nacional) o 3 horas antes (internacional),
  con devolución del 100 % al monedero.
- De las tarjetas solo se guardan los últimos cuatro dígitos.

## Trazabilidad: criterio de aceptación → prueba

### HU-010 · Reserva de tiquetes (CU-22, pantallas 12 y 13)

| Criterio | Pruebas |
| --- | --- |
| Pide los datos de cada viajero | `test_hu010_reserva.py`: `test_pide_los_datos_de_cada_viajero` (los 9 campos) |
| La reserva sin pago bloquea las sillas y vence a las 24 h | `test_reserva_sin_pagar_bloquea_sillas_…`, `test_vence_antes_si_el_vuelo_sale_…` · e2e «HU-010» |
| Silla aleatoria dentro de la clase | `test_cada_viajero_recibe_una_silla_aleatoria_de_la_clase`, `test_sin_sillas_suficientes_en_la_clase` |
| Máximo 5 tiquetes por vuelo | `test_no_acepta_sexto_tiquete_…`, `test_tiquetes_cancelados_no_cuentan_…` |
| Viajero repetido no se acepta | `test_no_acepta_viajero_repetido_en_el_mismo_vuelo` |
| Un menor no viaja solo | `test_menor_no_viaja_solo` · e2e «HU-010» |
| Ida y vuelta | `test_ida_y_vuelta_es_una_reserva_…`, `test_regreso_invalido` (2 casos) · e2e «HU-010» |
| Se puede reservar para terceros | `test_reserva_para_terceros` |

### HU-011 · Compra de tiquetes (CU-26, pantalla 15)

| Criterio | Pruebas |
| --- | --- |
| La compra genera un código único y se envía a cada viajero | `test_hu011_013_compra_pago.py`: `test_compra_genera_codigo_y_lo_envia_…`, `test_codigos_de_reserva_son_unicos` |
| La reserva queda pagada | `test_compra_genera_codigo_…` · e2e «HU-012 y HU-013» |
| No se paga dos veces ni una reserva ajena | `test_no_se_paga_dos_veces_ni_una_reserva_ajena` |

### HU-012 · Carrito (CU-25, pantalla 14)

| Criterio | Pruebas |
| --- | --- |
| Muestra subtotales y total | `test_hu012_carrito.py`: `test_muestra_subtotales_y_total` · e2e |
| Quitar una reserva actualiza el total | `test_retirar_actualiza_el_total_…` |
| Carrito vacío | `test_carrito_vacio` · e2e «HU-012 · carrito vacío» |
| Gestionar el carrito no cambia el saldo | `test_gestionar_el_carrito_no_toca_el_saldo` |

### HU-013 · Pago con monedero (CU-37)

| Criterio | Pruebas |
| --- | --- |
| Se descuenta el total con la referencia de la reserva | `test_pago_debita_el_monedero_con_referencia` · e2e |
| Saldo insuficiente: no se descuenta ni se compra | `test_saldo_insuficiente_rechaza_sin_debitar_ni_comprar` · e2e |
| Varias reservas en un solo pago | `test_paga_varias_reservas_del_carrito_…` |

### HU-014 · Monedero (CU-36, pantalla 16)

| Criterio | Pruebas |
| --- | --- |
| La tarjeta se guarda solo con los últimos 4 dígitos | `test_hu014_monedero.py`: `test_tarjeta_guarda_solo_los_ultimos_cuatro_digitos`, `test_tarjeta_invalida` · e2e |
| El ajuste manual queda como movimiento | `test_ajuste_manual_queda_como_movimiento` · e2e |
| Se ven débitos y abonos | `test_pago_debita_…`, `test_cancela_compra_dentro_del_plazo_…` · e2e |

### HU-015 · Cancelar compra (CU-27)

| Criterio | Pruebas |
| --- | --- |
| Dentro del plazo: reembolso del 100 % y sillas libres | `test_hu015_018_cancelaciones.py`: `test_cancela_compra_dentro_del_plazo_…` · e2e «HU-017 y HU-015» |
| Plazo de 1 h en nacionales y 3 h en internacionales | `test_nacional_no_se_cancela_a_menos_de_una_hora`, `test_nacional_se_cancela_con_mas_…`, `test_internacional_tiene_plazo_de_tres_horas` |
| No se cancela dos veces | `test_no_se_cancela_dos_veces` |

### HU-016 · Cancelar reserva (CU-28)

| Criterio | Pruebas |
| --- | --- |
| Solo reservas vigentes; las sillas se liberan | `test_cancela_reserva_vigente_y_libera_sillas`, `test_reserva_vencida_no_se_cancela` · e2e «HU-016» |

### HU-017 · Histórico (CU-29, pantallas 17 y 18)

| Criterio | Pruebas |
| --- | --- |
| Lista todas las reservas, también canceladas y vencidas, y muestra el detalle | `test_historico_lista_todas_y_muestra_el_detalle`, `test_historico_vacio` · e2e |

### HU-018 · Liberación por vencimiento

| Criterio | Pruebas |
| --- | --- |
| A las 24 h la reserva queda vencida y las sillas libres | `test_reserva_sin_pagar_se_libera_a_las_24_horas`, `test_tarea_periodica_libera_vencidas` |
| Antes de 24 h sigue vigente | `test_antes_de_24_horas_sigue_vigente` |
| Las compras pagadas no se liberan | `test_compras_pagadas_no_se_liberan` |

## Pantallas nuevas

| Ruta | Pantalla |
| --- | --- |
| `/reservar/[codigo]` | Clase, trayecto, viajeros y botones «Agregar al carrito» y «Comprar ahora» |
| `/cliente/carrito` | Carrito con subtotales, total y saldo |
| `/cliente/pago` | Confirmación del pago con el monedero |
| `/cliente/reservas` | Histórico |
| `/cliente/reservas/[codigo]` | Detalle, pago y cancelación |
| `/cliente/monedero` | Saldo, movimientos y tarjetas |

## Endpoints nuevos

`POST /reservas`, `GET /reservas`, `GET /reservas/{codigo}`, `POST /reservas/{codigo}/cancelar`, `POST /pagos`,
`GET /carrito`, `POST /carrito/{codigo}`, `DELETE /carrito/{codigo}`, `GET /monedero`, `POST /monedero/tarjetas`,
`DELETE /monedero/tarjetas/{id}`, `PUT /monedero/saldo`, `GET /vuelos/{codigo}/regresos`.
