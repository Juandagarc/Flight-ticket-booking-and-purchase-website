-- Modelo relacional · Sistema de gestión de compra y reserva de tiquetes aéreos en línea

-- Laboratorio de Software 2026-02 · UTP · Generado a partir del modelo E-R v1.0 (02/10/2026)

-- Motor: PostgreSQL 16 (el stack del equipo puede cambiar el motor; RNF-08).

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- USUARIO + ISA (ROOT, ADMINISTRADOR, CLIENTE): Cuenta de acceso. La especialización disjunta y total se resuelve con el discriminador rol (RF-27, RNF-05).

CREATE TABLE usuario (

id UUID NOT NULL DEFAULT gen_random_uuid(),

nombre_usuario VARCHAR(50) NOT NULL,

contrasena_hash VARCHAR(255) NOT NULL,

rol VARCHAR(13) NOT NULL,

activo BOOLEAN NOT NULL DEFAULT TRUE,

fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT now(),

CONSTRAINT pk_usuario PRIMARY KEY (id),

CONSTRAINT uq_usuario_1 UNIQUE (nombre_usuario),

CONSTRAINT ck_usuario_1 CHECK (rol IN ('ROOT', 'ADMINISTRADOR', 'CLIENTE'))

);

-- PERFIL + REGISTRA / COMPLETA: Datos personales del cliente (obligatorios) o del administrador (opcionales). El documento es el identificador único de la persona (RF-28, RF-32, RF-61).

CREATE TABLE perfil (

documento VARCHAR(20) NOT NULL,

usuario_id UUID NOT NULL,

tipo_documento VARCHAR(9) NOT NULL,

nombres VARCHAR(80) NOT NULL,

apellidos VARCHAR(80) NOT NULL,

fecha_nacimiento DATE NOT NULL,

lugar_nacimiento VARCHAR(100) NOT NULL,

direccion_facturacion VARCHAR(200) NOT NULL,

genero VARCHAR(10) NOT NULL,

correo VARCHAR(120) NOT NULL,

imagen_url VARCHAR(300) NULL,

CONSTRAINT pk_perfil PRIMARY KEY (documento),

CONSTRAINT uq_perfil_1 UNIQUE (usuario_id),

CONSTRAINT fk_perfil_1 FOREIGN KEY (usuario_id) REFERENCES usuario (id) ON DELETE CASCADE,

CONSTRAINT ck_perfil_1 CHECK (documento ~ '^[A-Za-z0-9]{4,20}$'),

CONSTRAINT ck_perfil_2 CHECK (tipo_documento IN ('CEDULA', 'PASAPORTE')),

CONSTRAINT ck_perfil_3 CHECK (genero IN ('FEMENINO', 'MASCULINO', 'OTRO'))

);

-- CIUDAD: Catálogo: 32 capitales departamentales, orígenes y destinos internacionales permitidos (RF-03 a RF-05, RF-49).

CREATE TABLE ciudad (

codigo VARCHAR(5) NOT NULL,

nombre VARCHAR(80) NOT NULL,

pais VARCHAR(60) NOT NULL,

zona_horaria VARCHAR(40) NOT NULL,

latitud NUMERIC(9,6) NOT NULL,

longitud NUMERIC(9,6) NOT NULL,

es_capital_nacional BOOLEAN NOT NULL DEFAULT FALSE,

origen_internacional BOOLEAN NOT NULL DEFAULT FALSE,

destino_internacional BOOLEAN NOT NULL DEFAULT FALSE,

CONSTRAINT pk_ciudad PRIMARY KEY (codigo)

);

-- CONFIGURACION_CABINA: Distribución fija del avión por tipo de vuelo (RF-43, RF-44, RF-76).

CREATE TABLE configuracion_cabina (

tipo_vuelo VARCHAR(13) NOT NULL,

capacidad SMALLINT NOT NULL,

ultima_silla_primera SMALLINT NOT NULL,

columnas VARCHAR(10) NOT NULL,

CONSTRAINT pk_configuracion_cabina PRIMARY KEY (tipo_vuelo),

CONSTRAINT ck_configuracion_cabina_1 CHECK (tipo_vuelo IN ('NACIONAL', 'INTERNACIONAL')),

CONSTRAINT ck_configuracion_cabina_2 CHECK (capacidad IN (150, 250)),

CONSTRAINT ck_configuracion_cabina_3 CHECK (ultima_silla_primera IN (25, 50))

);

-- SILLA (débil de CONFIGURACION_CABINA) + COMPUESTA_POR: Asientos de cada configuración, con clase y posición (RF-43 a RF-46).

CREATE TABLE silla (

tipo_vuelo VARCHAR(13) NOT NULL,

numero SMALLINT NOT NULL,

fila SMALLINT NOT NULL,

columna CHAR(1) NOT NULL,

posicion VARCHAR(7) NOT NULL,

clase VARCHAR(9) NOT NULL,

CONSTRAINT pk_silla PRIMARY KEY (tipo_vuelo, numero),

CONSTRAINT fk_silla_1 FOREIGN KEY (tipo_vuelo) REFERENCES configuracion_cabina (tipo_vuelo) ON DELETE CASCADE,

CONSTRAINT ck_silla_1 CHECK (numero > 0),

CONSTRAINT ck_silla_2 CHECK (posicion IN ('VENTANA', 'CENTRO', 'PASILLO')),

CONSTRAINT ck_silla_3 CHECK (clase IN ('PRIMERA', 'ECONOMICA'))

);

-- VUELO + ORIGEN + DESTINO + USA + PROGRAMA: Vuelo directo programado. El código se autogenera y la duración y la llegada se calculan (RF-01, RF-02, RF-06, RF-53, RF-54).

CREATE TABLE vuelo (

codigo VARCHAR(10) NOT NULL,

tipo VARCHAR(13) NOT NULL,

origen VARCHAR(5) NOT NULL,

destino VARCHAR(5) NOT NULL,

fecha_hora_salida TIMESTAMPTZ NOT NULL,

duracion_min INTEGER NOT NULL,

llegada_local TIMESTAMP NOT NULL,

estado VARCHAR(10) NOT NULL DEFAULT 'PROGRAMADO',

imagen_url VARCHAR(300) NOT NULL,

administrador_id UUID NOT NULL,

fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT now(),

CONSTRAINT pk_vuelo PRIMARY KEY (codigo),

CONSTRAINT uq_vuelo_1 UNIQUE (codigo, tipo),

CONSTRAINT fk_vuelo_1 FOREIGN KEY (tipo) REFERENCES configuracion_cabina (tipo_vuelo),

CONSTRAINT fk_vuelo_2 FOREIGN KEY (origen) REFERENCES ciudad (codigo),

CONSTRAINT fk_vuelo_3 FOREIGN KEY (destino) REFERENCES ciudad (codigo),

CONSTRAINT fk_vuelo_4 FOREIGN KEY (administrador_id) REFERENCES usuario (id),

CONSTRAINT ck_vuelo_1 CHECK (origen <> destino),

CONSTRAINT ck_vuelo_2 CHECK (duracion_min > 0),

CONSTRAINT ck_vuelo_3 CHECK (estado IN ('PROGRAMADO', 'CANCELADO', 'REALIZADO')),

CONSTRAINT ck_vuelo_4 CHECK (codigo ~ '^[A-Z]{2}[0-9]+$')

);

-- TARIFA (débil de VUELO) + COBRA: Costo por persona en cada clase (RF-01, RF-21).

CREATE TABLE tarifa (

vuelo_codigo VARCHAR(10) NOT NULL,

clase VARCHAR(9) NOT NULL,

valor NUMERIC(14,2) NOT NULL,

CONSTRAINT pk_tarifa PRIMARY KEY (vuelo_codigo, clase),

CONSTRAINT fk_tarifa_1 FOREIGN KEY (vuelo_codigo) REFERENCES vuelo (codigo) ON DELETE CASCADE,

CONSTRAINT ck_tarifa_1 CHECK (clase IN ('PRIMERA', 'ECONOMICA')),

CONSTRAINT ck_tarifa_2 CHECK (valor > 0)

);

-- PROMOCION + OFRECE: Rebaja en porcentaje o valor fijo, con vigencia, para los cupos disponibles (RF-11).

CREATE TABLE promocion (

id UUID NOT NULL DEFAULT gen_random_uuid(),

vuelo_codigo VARCHAR(10) NOT NULL,

tipo_descuento VARCHAR(10) NOT NULL,

valor NUMERIC(14,2) NOT NULL,

fecha_inicio TIMESTAMPTZ NOT NULL,

fecha_fin TIMESTAMPTZ NOT NULL,

activa BOOLEAN NOT NULL DEFAULT TRUE,

CONSTRAINT pk_promocion PRIMARY KEY (id),

CONSTRAINT fk_promocion_1 FOREIGN KEY (vuelo_codigo) REFERENCES vuelo (codigo) ON DELETE CASCADE,

CONSTRAINT ck_promocion_1 CHECK (tipo_descuento IN ('PORCENTAJE', 'VALOR_FIJO')),

CONSTRAINT ck_promocion_2 CHECK (valor > 0),

CONSTRAINT ck_promocion_3 CHECK (fecha_fin > fecha_inicio)

);

-- CAUSAL_FUERZA_MAYOR: Causales parametrizables de cancelación por fuerza mayor (RF-50).

CREATE TABLE causal_fuerza_mayor (

id SMALLINT GENERATED ALWAYS AS IDENTITY,

nombre VARCHAR(60) NOT NULL,

descripcion VARCHAR(200) NULL,

activa BOOLEAN NOT NULL DEFAULT TRUE,

CONSTRAINT pk_causal_fuerza_mayor PRIMARY KEY (id),

CONSTRAINT uq_causal_fuerza_mayor_1 UNIQUE (nombre)

);

-- CANCELACION_VUELO + SE_CANCELA + JUSTIFICA: Cancelación ordinaria, por fuerza mayor o por no vender tiquetes (RF-08, RF-50, RF-52).

CREATE TABLE cancelacion_vuelo (

id UUID NOT NULL DEFAULT gen_random_uuid(),

vuelo_codigo VARCHAR(10) NOT NULL,

tipo VARCHAR(12) NOT NULL,

causal_id SMALLINT NULL,

fecha TIMESTAMPTZ NOT NULL DEFAULT now(),

observacion VARCHAR(300) NULL,

CONSTRAINT pk_cancelacion_vuelo PRIMARY KEY (id),

CONSTRAINT uq_cancelacion_vuelo_1 UNIQUE (vuelo_codigo),

CONSTRAINT fk_cancelacion_vuelo_1 FOREIGN KEY (vuelo_codigo) REFERENCES vuelo (codigo),

CONSTRAINT fk_cancelacion_vuelo_2 FOREIGN KEY (causal_id) REFERENCES causal_fuerza_mayor (id),

CONSTRAINT ck_cancelacion_vuelo_1 CHECK (tipo IN ('ORDINARIA', 'FUERZA_MAYOR', 'SIN_VENTAS')),

CONSTRAINT ck_cancelacion_vuelo_2 CHECK ((tipo = 'FUERZA_MAYOR') = (causal_id IS NOT NULL))

);

-- MONEDERO + POSEE: Monedero interno y simulado de cada cliente (RF-30, RF-38, RF-70, RF-71). El saldo no puede quedar negativo.

CREATE TABLE monedero (

id UUID NOT NULL DEFAULT gen_random_uuid(),

cliente_id UUID NOT NULL,

saldo NUMERIC(14,2) NOT NULL DEFAULT 0,

CONSTRAINT pk_monedero PRIMARY KEY (id),

CONSTRAINT uq_monedero_1 UNIQUE (cliente_id),

CONSTRAINT fk_monedero_1 FOREIGN KEY (cliente_id) REFERENCES usuario (id) ON DELETE CASCADE,

CONSTRAINT ck_monedero_1 CHECK (saldo >= 0)

);

-- TARJETA + REGISTRA: Tarjetas informativas del monedero; solo se guardan los últimos dígitos (RF-38).

CREATE TABLE tarjeta (

id UUID NOT NULL DEFAULT gen_random_uuid(),

monedero_id UUID NOT NULL,

tipo VARCHAR(7) NOT NULL,

franquicia VARCHAR(30) NOT NULL,

titular VARCHAR(120) NOT NULL,

ultimos_digitos CHAR(4) NOT NULL,

vencimiento CHAR(5) NOT NULL,

CONSTRAINT pk_tarjeta PRIMARY KEY (id),

CONSTRAINT fk_tarjeta_1 FOREIGN KEY (monedero_id) REFERENCES monedero (id) ON DELETE CASCADE,

CONSTRAINT ck_tarjeta_1 CHECK (tipo IN ('CREDITO', 'DEBITO')),

CONSTRAINT ck_tarjeta_2 CHECK (ultimos_digitos ~ '^[0-9]{4}$')

);

-- MOVIMIENTO + ACUMULA: Cada cambio de saldo: recarga, ajuste manual, débito por compra o abono por reembolso (RF-72).

CREATE TABLE movimiento_monedero (

id UUID NOT NULL DEFAULT gen_random_uuid(),

monedero_id UUID NOT NULL,

tipo VARCHAR(16) NOT NULL,

monto NUMERIC(14,2) NOT NULL,

fecha TIMESTAMPTZ NOT NULL DEFAULT now(),

saldo_resultante NUMERIC(14,2) NOT NULL,

descripcion VARCHAR(200) NULL,

CONSTRAINT pk_movimiento_monedero PRIMARY KEY (id),

CONSTRAINT fk_movimiento_monedero_1 FOREIGN KEY (monedero_id) REFERENCES monedero (id) ON DELETE CASCADE,

CONSTRAINT ck_movimiento_monedero_1 CHECK (tipo IN ('RECARGA', 'AJUSTE_MANUAL', 'DEBITO_COMPRA', 'ABONO_REEMBOLSO'))

);

-- PAGO + DEBITA + GENERA: Transacción simulada que paga en una sola operación las reservas del carrito (RF-57, RF-71).

CREATE TABLE pago (

id UUID NOT NULL DEFAULT gen_random_uuid(),

monedero_id UUID NOT NULL,

movimiento_id UUID NULL,

fecha TIMESTAMPTZ NOT NULL DEFAULT now(),

monto_total NUMERIC(14,2) NOT NULL,

estado VARCHAR(9) NOT NULL,

CONSTRAINT pk_pago PRIMARY KEY (id),

CONSTRAINT uq_pago_1 UNIQUE (movimiento_id),

CONSTRAINT fk_pago_1 FOREIGN KEY (monedero_id) REFERENCES monedero (id),

CONSTRAINT fk_pago_2 FOREIGN KEY (movimiento_id) REFERENCES movimiento_monedero (id),

CONSTRAINT ck_pago_1 CHECK (monto_total > 0),

CONSTRAINT ck_pago_2 CHECK (estado IN ('APROBADO', 'RECHAZADO'))

);

-- CARRITO + TIENE: Carrito único de cada cliente; admite vuelos distintos (RF-18, RF-57).

CREATE TABLE carrito (

id UUID NOT NULL DEFAULT gen_random_uuid(),

cliente_id UUID NOT NULL,

fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT now(),

CONSTRAINT pk_carrito PRIMARY KEY (id),

CONSTRAINT uq_carrito_1 UNIQUE (cliente_id),

CONSTRAINT fk_carrito_1 FOREIGN KEY (cliente_id) REFERENCES usuario (id) ON DELETE CASCADE

);

-- RESERVA + REALIZA + CONTIENE + CUBRE: Reserva o compra: se diferencian solo en el pago y ambas bloquean sillas; la reserva sin pago vence a las 24 h (RF-14, RF-55).

CREATE TABLE reserva (

codigo CHAR(6) NOT NULL,

cliente_id UUID NOT NULL,

carrito_id UUID NULL,

pago_id UUID NULL,

estado VARCHAR(12) NOT NULL,

tipo_trayecto VARCHAR(12) NOT NULL,

fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT now(),

fecha_expiracion TIMESTAMPTZ NULL,

total NUMERIC(14,2) NOT NULL DEFAULT 0,

CONSTRAINT pk_reserva PRIMARY KEY (codigo),

CONSTRAINT fk_reserva_1 FOREIGN KEY (cliente_id) REFERENCES usuario (id),

CONSTRAINT fk_reserva_2 FOREIGN KEY (carrito_id) REFERENCES carrito (id) ON DELETE SET NULL,

CONSTRAINT fk_reserva_3 FOREIGN KEY (pago_id) REFERENCES pago (id),

CONSTRAINT ck_reserva_1 CHECK (estado IN ('RESERVADA', 'PAGADA', 'CANCELADA', 'VENCIDA', 'REPROGRAMADA')),

CONSTRAINT ck_reserva_2 CHECK (tipo_trayecto IN ('SENCILLO', 'IDA_Y_VUELTA')),

CONSTRAINT ck_reserva_3 CHECK (estado <> 'RESERVADA' OR fecha_expiracion IS NOT NULL),

CONSTRAINT ck_reserva_4 CHECK (estado <> 'PAGADA' OR pago_id IS NOT NULL)

);

-- PASAJERO + CORRESPONDE: Viajero de una compra, tenga o no cuenta; si es cliente registrado se enlaza para autocompletar (RF-16, RF-41, RF-56).

CREATE TABLE pasajero (

documento VARCHAR(20) NOT NULL,

nombres VARCHAR(80) NOT NULL,

apellidos VARCHAR(80) NOT NULL,

fecha_nacimiento DATE NOT NULL,

genero VARCHAR(10) NOT NULL,

telefono VARCHAR(20) NOT NULL,

correo VARCHAR(120) NOT NULL,

nombre_contacto VARCHAR(120) NOT NULL,

telefono_contacto VARCHAR(20) NOT NULL,

cliente_id UUID NULL,

CONSTRAINT pk_pasajero PRIMARY KEY (documento),

CONSTRAINT uq_pasajero_1 UNIQUE (cliente_id),

CONSTRAINT fk_pasajero_1 FOREIGN KEY (cliente_id) REFERENCES usuario (id) ON DELETE SET NULL

);

-- TIQUETE + INCLUYE + PARA + EMITIDO_A + OCUPA: Derecho de un pasajero a viajar en un vuelo y una silla (RF-15 a RF-17, RF-20, RF-21, RF-45).

CREATE TABLE tiquete (

id UUID NOT NULL DEFAULT gen_random_uuid(),

reserva_codigo CHAR(6) NOT NULL,

vuelo_codigo VARCHAR(10) NOT NULL,

tipo_vuelo VARCHAR(13) NOT NULL,

pasajero_documento VARCHAR(20) NOT NULL,

silla_numero SMALLINT NOT NULL,

clase VARCHAR(9) NOT NULL,

precio NUMERIC(14,2) NOT NULL,

estado VARCHAR(11) NOT NULL DEFAULT 'ACTIVO',

cambio_silla_usado BOOLEAN NOT NULL DEFAULT FALSE,

CONSTRAINT pk_tiquete PRIMARY KEY (id),

CONSTRAINT fk_tiquete_1 FOREIGN KEY (reserva_codigo) REFERENCES reserva (codigo) ON DELETE CASCADE,

CONSTRAINT fk_tiquete_2 FOREIGN KEY (vuelo_codigo, tipo_vuelo) REFERENCES vuelo (codigo, tipo),

CONSTRAINT fk_tiquete_3 FOREIGN KEY (pasajero_documento) REFERENCES pasajero (documento),

CONSTRAINT fk_tiquete_4 FOREIGN KEY (tipo_vuelo, silla_numero) REFERENCES silla (tipo_vuelo, numero),

CONSTRAINT ck_tiquete_1 CHECK (clase IN ('PRIMERA', 'ECONOMICA')),

CONSTRAINT ck_tiquete_2 CHECK (estado IN ('ACTIVO', 'CON_CHECKIN', 'CANCELADO')),

CONSTRAINT ck_tiquete_3 CHECK (precio >= 0)

);

CREATE UNIQUE INDEX ux_tiquete_pasajero_vuelo ON tiquete (vuelo_codigo, pasajero_documento) WHERE estado <> 'CANCELADO';

CREATE UNIQUE INDEX ux_tiquete_silla_vuelo ON tiquete (vuelo_codigo, silla_numero) WHERE estado <> 'CANCELADO';

-- REEMBOLSO + DEVUELVE + ABONA: Devolución del 100 % sin penalidad, abonada al monedero (RF-22, RF-72, RF-82).

CREATE TABLE reembolso (

id UUID NOT NULL DEFAULT gen_random_uuid(),

reserva_codigo CHAR(6) NOT NULL,

movimiento_id UUID NOT NULL,

monto NUMERIC(14,2) NOT NULL,

fecha TIMESTAMPTZ NOT NULL DEFAULT now(),

motivo VARCHAR(19) NOT NULL,

CONSTRAINT pk_reembolso PRIMARY KEY (id),

CONSTRAINT uq_reembolso_1 UNIQUE (reserva_codigo),

CONSTRAINT uq_reembolso_2 UNIQUE (movimiento_id),

CONSTRAINT fk_reembolso_1 FOREIGN KEY (reserva_codigo) REFERENCES reserva (codigo),

CONSTRAINT fk_reembolso_2 FOREIGN KEY (movimiento_id) REFERENCES movimiento_monedero (id),

CONSTRAINT ck_reembolso_1 CHECK (monto > 0),

CONSTRAINT ck_reembolso_2 CHECK (motivo IN ('CANCELACION_CLIENTE', 'CANCELACION_VUELO'))

);

-- AFECTACION + ORIGINA + AFECTA + REUBICA_EN + PRODUCE: Decisión del comprador ante la cancelación del vuelo: reembolso íntegro o reprogramación (RF-12, RF-51).

CREATE TABLE afectacion_vuelo (

id UUID NOT NULL DEFAULT gen_random_uuid(),

cancelacion_id UUID NOT NULL,

reserva_codigo CHAR(6) NOT NULL,

decision VARCHAR(14) NOT NULL DEFAULT 'PENDIENTE',

fecha_notificacion TIMESTAMPTZ NOT NULL DEFAULT now(),

fecha_decision TIMESTAMPTZ NULL,

reserva_nueva_codigo CHAR(6) NULL,

reembolso_id UUID NULL,

CONSTRAINT pk_afectacion_vuelo PRIMARY KEY (id),

CONSTRAINT uq_afectacion_vuelo_1 UNIQUE (cancelacion_id, reserva_codigo),

CONSTRAINT uq_afectacion_vuelo_2 UNIQUE (reserva_nueva_codigo),

CONSTRAINT uq_afectacion_vuelo_3 UNIQUE (reembolso_id),

CONSTRAINT fk_afectacion_vuelo_1 FOREIGN KEY (cancelacion_id) REFERENCES cancelacion_vuelo (id),

CONSTRAINT fk_afectacion_vuelo_2 FOREIGN KEY (reserva_codigo) REFERENCES reserva (codigo),

CONSTRAINT fk_afectacion_vuelo_3 FOREIGN KEY (reserva_nueva_codigo) REFERENCES reserva (codigo),

CONSTRAINT fk_afectacion_vuelo_4 FOREIGN KEY (reembolso_id) REFERENCES reembolso (id),

CONSTRAINT ck_afectacion_vuelo_1 CHECK (decision IN ('PENDIENTE', 'REEMBOLSO', 'REPROGRAMACION')),

CONSTRAINT ck_afectacion_vuelo_2 CHECK (decision <> 'REEMBOLSO' OR reembolso_id IS NOT NULL),

CONSTRAINT ck_afectacion_vuelo_3 CHECK (decision <> 'REPROGRAMACION' OR reserva_nueva_codigo IS NOT NULL)

);

-- CHECKIN + CONFIRMA + REALIZA: Check-in rápido (código o documento) o registrado (quien compró lo hace por todos) (RF-39 a RF-41, RF-73).

CREATE TABLE checkin (

id UUID NOT NULL DEFAULT gen_random_uuid(),

tiquete_id UUID NOT NULL,

modalidad VARCHAR(16) NOT NULL,

fecha TIMESTAMPTZ NOT NULL DEFAULT now(),

realizado_por UUID NULL,

CONSTRAINT pk_checkin PRIMARY KEY (id),

CONSTRAINT uq_checkin_1 UNIQUE (tiquete_id),

CONSTRAINT fk_checkin_1 FOREIGN KEY (tiquete_id) REFERENCES tiquete (id),

CONSTRAINT fk_checkin_2 FOREIGN KEY (realizado_por) REFERENCES usuario (id),

CONSTRAINT ck_checkin_1 CHECK (modalidad IN ('RAPIDA_CODIGO', 'RAPIDA_DOCUMENTO', 'REGISTRADA')),

CONSTRAINT ck_checkin_2 CHECK ((modalidad = 'REGISTRADA') = (realizado_por IS NOT NULL))

);

-- PASABORDO + EMITE: PDF del pasajero enviado por correo al confirmar el check-in (RF-42, RNF-04).

CREATE TABLE pasabordo (

id UUID NOT NULL DEFAULT gen_random_uuid(),

checkin_id UUID NOT NULL,

archivo_url VARCHAR(300) NOT NULL,

fecha_emision TIMESTAMPTZ NOT NULL DEFAULT now(),

correo_destino VARCHAR(120) NOT NULL,

CONSTRAINT pk_pasabordo PRIMARY KEY (id),

CONSTRAINT uq_pasabordo_1 UNIQUE (checkin_id),

CONSTRAINT fk_pasabordo_1 FOREIGN KEY (checkin_id) REFERENCES checkin (id) ON DELETE CASCADE

);

-- CAMBIO_SILLA + REGISTRA + DESDE + HACIA: Único cambio de silla por tiquete, antes del check-in (RF-45, RF-74, RF-75).

CREATE TABLE cambio_silla (

id UUID NOT NULL DEFAULT gen_random_uuid(),

tiquete_id UUID NOT NULL,

tipo_vuelo VARCHAR(13) NOT NULL,

silla_anterior SMALLINT NOT NULL,

silla_nueva SMALLINT NOT NULL,

fecha TIMESTAMPTZ NOT NULL DEFAULT now(),

CONSTRAINT pk_cambio_silla PRIMARY KEY (id),

CONSTRAINT uq_cambio_silla_1 UNIQUE (tiquete_id),

CONSTRAINT fk_cambio_silla_1 FOREIGN KEY (tiquete_id) REFERENCES tiquete (id) ON DELETE CASCADE,

CONSTRAINT fk_cambio_silla_2 FOREIGN KEY (tipo_vuelo, silla_anterior) REFERENCES silla (tipo_vuelo, numero),

CONSTRAINT fk_cambio_silla_3 FOREIGN KEY (tipo_vuelo, silla_nueva) REFERENCES silla (tipo_vuelo, numero),

CONSTRAINT ck_cambio_silla_1 CHECK (silla_anterior <> silla_nueva)

);

-- NOTICIA + ANUNCIA + DIFUNDE: Catálogo público de vuelos creados y promociones (RF-10, RF-11, RF-64, RF-65).

CREATE TABLE noticia (

id UUID NOT NULL DEFAULT gen_random_uuid(),

vuelo_codigo VARCHAR(10) NOT NULL,

promocion_id UUID NULL,

tipo VARCHAR(11) NOT NULL,

titulo VARCHAR(150) NOT NULL,

imagen_url VARCHAR(300) NOT NULL,

precio_unitario NUMERIC(14,2) NOT NULL,

fecha_publicacion TIMESTAMPTZ NOT NULL DEFAULT now(),

vigente BOOLEAN NOT NULL DEFAULT TRUE,

CONSTRAINT pk_noticia PRIMARY KEY (id),

CONSTRAINT uq_noticia_1 UNIQUE (promocion_id),

CONSTRAINT fk_noticia_1 FOREIGN KEY (vuelo_codigo) REFERENCES vuelo (codigo) ON DELETE CASCADE,

CONSTRAINT fk_noticia_2 FOREIGN KEY (promocion_id) REFERENCES promocion (id) ON DELETE SET NULL,

CONSTRAINT ck_noticia_1 CHECK (tipo IN ('NUEVO_VUELO', 'PROMOCION')),

CONSTRAINT ck_noticia_2 CHECK ((tipo = 'PROMOCION') = (promocion_id IS NOT NULL))

);

-- SUSCRIPCION + TIENE: Suscripción del cliente con perfil completo a las novedades (RF-29, RF-35, RF-66).

CREATE TABLE suscripcion (

id UUID NOT NULL DEFAULT gen_random_uuid(),

cliente_id UUID NOT NULL,

fecha_alta TIMESTAMPTZ NOT NULL DEFAULT now(),

activa BOOLEAN NOT NULL DEFAULT TRUE,

CONSTRAINT pk_suscripcion PRIMARY KEY (id),

CONSTRAINT uq_suscripcion_1 UNIQUE (cliente_id),

CONSTRAINT fk_suscripcion_1 FOREIGN KEY (cliente_id) REFERENCES usuario (id) ON DELETE CASCADE

);

-- NOTIFICACION + RECIBE + AVISA: Aviso de cada vuelo creado a los suscriptores, por correo y en la aplicación (RF-66, RF-67).

CREATE TABLE notificacion (

id UUID NOT NULL DEFAULT gen_random_uuid(),

suscripcion_id UUID NOT NULL,

noticia_id UUID NOT NULL,

canal VARCHAR(10) NOT NULL,

fecha_envio TIMESTAMPTZ NULL,

enviada BOOLEAN NOT NULL DEFAULT FALSE,

leida BOOLEAN NOT NULL DEFAULT FALSE,

CONSTRAINT pk_notificacion PRIMARY KEY (id),

CONSTRAINT uq_notificacion_1 UNIQUE (suscripcion_id, noticia_id, canal),

CONSTRAINT fk_notificacion_1 FOREIGN KEY (suscripcion_id) REFERENCES suscripcion (id) ON DELETE CASCADE,

CONSTRAINT fk_notificacion_2 FOREIGN KEY (noticia_id) REFERENCES noticia (id) ON DELETE CASCADE,

CONSTRAINT ck_notificacion_1 CHECK (canal IN ('CORREO', 'APLICACION'))

);

-- CONVERSACION + INICIA + ATIENDE: Hilo de mensajería entre un cliente y la administración, con respuesta diferida (RF-36).

CREATE TABLE conversacion (

id UUID NOT NULL DEFAULT gen_random_uuid(),

cliente_id UUID NOT NULL,

administrador_id UUID NULL,

asunto VARCHAR(150) NOT NULL,

fecha_inicio TIMESTAMPTZ NOT NULL DEFAULT now(),

estado VARCHAR(7) NOT NULL DEFAULT 'ABIERTA',

CONSTRAINT pk_conversacion PRIMARY KEY (id),

CONSTRAINT fk_conversacion_1 FOREIGN KEY (cliente_id) REFERENCES usuario (id),

CONSTRAINT fk_conversacion_2 FOREIGN KEY (administrador_id) REFERENCES usuario (id),

CONSTRAINT ck_conversacion_1 CHECK (estado IN ('ABIERTA', 'CERRADA'))

);

-- MENSAJE + CONTIENE + ESCRIBE: Mensaje dentro de una conversación (RF-36).

CREATE TABLE mensaje (

id UUID NOT NULL DEFAULT gen_random_uuid(),

conversacion_id UUID NOT NULL,

autor_id UUID NOT NULL,

texto TEXT NOT NULL,

fecha TIMESTAMPTZ NOT NULL DEFAULT now(),

leido BOOLEAN NOT NULL DEFAULT FALSE,

CONSTRAINT pk_mensaje PRIMARY KEY (id),

CONSTRAINT fk_mensaje_1 FOREIGN KEY (conversacion_id) REFERENCES conversacion (id) ON DELETE CASCADE,

CONSTRAINT fk_mensaje_2 FOREIGN KEY (autor_id) REFERENCES usuario (id)

);

-- CONVERSACION_CHATBOT + CONVERSA: Conversación unipersonal con el asistente; la de un visitante solo tiene sesión (RF-48, RF-79).

CREATE TABLE conversacion_chatbot (

id UUID NOT NULL DEFAULT gen_random_uuid(),

cliente_id UUID NULL,

sesion_id VARCHAR(64) NOT NULL,

contexto VARCHAR(9) NOT NULL,

fecha_inicio TIMESTAMPTZ NOT NULL DEFAULT now(),

CONSTRAINT pk_conversacion_chatbot PRIMARY KEY (id),

CONSTRAINT fk_conversacion_chatbot_1 FOREIGN KEY (cliente_id) REFERENCES usuario (id) ON DELETE SET NULL,

CONSTRAINT ck_conversacion_chatbot_1 CHECK (contexto IN ('VISITANTE', 'CLIENTE')),

CONSTRAINT ck_conversacion_chatbot_2 CHECK ((contexto = 'CLIENTE') = (cliente_id IS NOT NULL))

);

-- MENSAJE_CHATBOT + INCLUYE: Turno de la conversación con el asistente basado en reglas (RF-80).

CREATE TABLE mensaje_chatbot (

id UUID NOT NULL DEFAULT gen_random_uuid(),

conversacion_id UUID NOT NULL,

emisor VARCHAR(9) NOT NULL,

texto TEXT NOT NULL,

intencion VARCHAR(60) NULL,

fecha TIMESTAMPTZ NOT NULL DEFAULT now(),

CONSTRAINT pk_mensaje_chatbot PRIMARY KEY (id),

CONSTRAINT fk_mensaje_chatbot_1 FOREIGN KEY (conversacion_id) REFERENCES conversacion_chatbot (id) ON DELETE CASCADE,

CONSTRAINT ck_mensaje_chatbot_1 CHECK (emisor IN ('USUARIO', 'ASISTENTE'))

);

-- ACTIVIDAD + GENERA + SOBRE: Búsquedas, reservas y compras de cada cliente: insumo del recomendador (RF-60, RF-77).

CREATE TABLE actividad_usuario (

id UUID NOT NULL DEFAULT gen_random_uuid(),

cliente_id UUID NOT NULL,

tipo VARCHAR(8) NOT NULL,

fecha TIMESTAMPTZ NOT NULL DEFAULT now(),

vuelo_codigo VARCHAR(10) NULL,

origen VARCHAR(5) NULL,

destino VARCHAR(5) NULL,

fecha_desde DATE NULL,

fecha_hasta DATE NULL,

precio_min NUMERIC(14,2) NULL,

precio_max NUMERIC(14,2) NULL,

pasajeros SMALLINT NULL,

tipo_trayecto VARCHAR(12) NULL,

CONSTRAINT pk_actividad_usuario PRIMARY KEY (id),

CONSTRAINT fk_actividad_usuario_1 FOREIGN KEY (cliente_id) REFERENCES usuario (id) ON DELETE CASCADE,

CONSTRAINT fk_actividad_usuario_2 FOREIGN KEY (vuelo_codigo) REFERENCES vuelo (codigo) ON DELETE SET NULL,

CONSTRAINT ck_actividad_usuario_1 CHECK (tipo IN ('BUSQUEDA', 'RESERVA', 'COMPRA'))

);

CREATE INDEX ix_actividad_cliente_fecha ON actividad_usuario (cliente_id, fecha DESC);

-- RECOMENDACION + RECIBE + SUGIERE: Vuelo sugerido a un cliente con su motivo; sin histórico, los más comprados (RF-47, RF-77, RF-78).

CREATE TABLE recomendacion (

id UUID NOT NULL DEFAULT gen_random_uuid(),

cliente_id UUID NOT NULL,

vuelo_codigo VARCHAR(10) NOT NULL,

puntaje NUMERIC(5,2) NOT NULL,

motivo VARCHAR(200) NOT NULL,

fecha_generacion TIMESTAMPTZ NOT NULL DEFAULT now(),

CONSTRAINT pk_recomendacion PRIMARY KEY (id),

CONSTRAINT fk_recomendacion_1 FOREIGN KEY (cliente_id) REFERENCES usuario (id) ON DELETE CASCADE,

CONSTRAINT fk_recomendacion_2 FOREIGN KEY (vuelo_codigo) REFERENCES vuelo (codigo) ON DELETE CASCADE

);

-- Datos fijos que exige el enunciado -------------------------------------------------

INSERT INTO configuracion_cabina (tipo_vuelo, capacidad, ultima_silla_primera, columnas) VALUES

('NACIONAL', 150, 25, 'ABC-DEF'),

('INTERNACIONAL', 250, 50, 'ABC-DEF');

-- Sillas numeradas 1..capacidad en filas de 6 columnas (A-F); A/F ventana, B/E centro, C/D pasillo.

INSERT INTO silla (tipo_vuelo, numero, fila, columna, posicion, clase)

SELECT c.tipo_vuelo, n, (n - 1) / 6 + 1, substr('ABCDEF', ((n - 1) % 6) + 1, 1),

CASE ((n - 1) % 6) WHEN 0 THEN 'VENTANA' WHEN 5 THEN 'VENTANA'

WHEN 1 THEN 'CENTRO' WHEN 4 THEN 'CENTRO' ELSE 'PASILLO' END,

CASE WHEN n <= c.ultima_silla_primera THEN 'PRIMERA' ELSE 'ECONOMICA' END

FROM configuracion_cabina c CROSS JOIN LATERAL generate_series(1, c.capacidad) AS n;

INSERT INTO causal_fuerza_mayor (nombre, descripcion) VALUES

('Terremoto', 'Evento sísmico que impide operar'),

('Huelga', 'Cese de actividades del personal'),

('Pista inhabilitada', 'Pista dañada o cerrada'),

('Avería de la aeronave', 'Falla técnica del avión'),

('Mal tiempo', 'Condiciones meteorológicas adversas');

-- Usuario root creado por defecto (RF-31). La contraseña real se define al desplegar.

INSERT INTO usuario (nombre_usuario, contrasena_hash, rol) VALUES ('root', 'CAMBIAR_AL_DESPLEGAR', 'ROOT');

