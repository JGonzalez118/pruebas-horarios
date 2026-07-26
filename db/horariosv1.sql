-- =====================================================================
-- SISTEMA DE GESTION DE HORARIOS UNIVERSITARIOS - VERSION 4 + GA-EXT
-- Base de datos independiente para la API de pruebas del algoritmo
-- genetico. Es una copia completa del schema v4 FINAL con los campos
-- de creditos academicos y calificacion docente-materia YA integrados
-- desde la definicion de las tablas (sin ALTER TABLE posteriores).
--
-- Listo para importar directo en MariaDB 12.3.2 (Laragon / Docker).
-- Crea la base de datos, la selecciona, y define las 23 tablas
-- (las 22 originales + calificaciones_docente_materia).
-- =====================================================================

CREATE DATABASE IF NOT EXISTS sistema_horarios_ga
CHARACTER SET utf8mb4
COLLATE utf8mb4_general_ci;

USE sistema_horarios_ga;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;


-- ---------------------------------------------------------------------
-- 1. CATALOGOS BASE (organizacion academica)
-- ---------------------------------------------------------------------

CREATE TABLE roles (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre_rol VARCHAR(50) NOT NULL,
    descripcion VARCHAR(255),
    creado DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modificado DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_roles_nombre (nombre_rol)
) ENGINE=InnoDB;

CREATE TABLE `facultades` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `codigo_facultad` VARCHAR(50) NOT NULL,
    `nombre` VARCHAR(150) NOT NULL,
    `activo` BOOLEAN NOT NULL DEFAULT TRUE,
    `creado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `modificado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_facultades_codigo` (`codigo_facultad`)
) ENGINE=InnoDB;

CREATE TABLE `departamentos` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `facultad_id` INT UNSIGNED NOT NULL,
    `nombre` VARCHAR(150) NOT NULL,
    `descripcion` VARCHAR(255),
    `activo` BOOLEAN NOT NULL DEFAULT TRUE,
    `creado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `modificado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_departamentos_facultad` (`facultad_id`),
    CONSTRAINT `fk_departamentos_facultad`
        FOREIGN KEY (`facultad_id`) REFERENCES `facultades` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- usuarios = personas que ACCEDEN al sistema (admins, coordinadores, etc).
-- Los profesores NO son usuarios; son entidades academicas independientes.
CREATE TABLE `usuarios` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `rol_id` INT UNSIGNED NOT NULL,
    `departamento_id` INT UNSIGNED,
    `cedula` VARCHAR(50) NOT NULL,
    `nombre` VARCHAR(100) NOT NULL,
    `apellido` VARCHAR(100) NOT NULL,
    `correo` VARCHAR(100) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `estado_cuenta` VARCHAR(20) NOT NULL DEFAULT 'Activa',
    `intentos_fallidos` INT UNSIGNED NOT NULL DEFAULT 0,
    `ultimo_login` DATETIME,
    `creado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `modificado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_usuarios_cedula` (`cedula`),
    UNIQUE KEY `uq_usuarios_correo` (`correo`),
    KEY `idx_usuarios_rol` (`rol_id`),
    KEY `idx_usuarios_departamento` (`departamento_id`),
    CONSTRAINT `fk_usuarios_rol`
        FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_usuarios_departamento`
        FOREIGN KEY (`departamento_id`) REFERENCES `departamentos` (`id`)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- NUEVO: creditos_academicos -> creditos del escalafon docente del
-- profesor. Junto con departamento_id y la calificacion por materia
-- (ver calificaciones_docente_materia mas abajo), determina que
-- materias puede impartir.
CREATE TABLE `profesores` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `departamento_id` INT UNSIGNED NOT NULL,
    `cedula` VARCHAR(50) NOT NULL,
    `nombre` VARCHAR(100) NOT NULL,
    `apellido` VARCHAR(100) NOT NULL,
    `correo` VARCHAR(100),
    `creditos_academicos` INT UNSIGNED NOT NULL DEFAULT 0
        COMMENT 'Creditos acumulados en el escalafon docente',
    `activo` BOOLEAN NOT NULL DEFAULT TRUE,
    `creado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `modificado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_profesores_cedula` (`cedula`),
    KEY `idx_profesores_departamento` (`departamento_id`),
    CONSTRAINT `fk_profesores_departamento`
        FOREIGN KEY (`departamento_id`) REFERENCES `departamentos` (`id`)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE `carreras` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `facultad_id` INT UNSIGNED NOT NULL,
    `codigo_carrera` VARCHAR(50) NOT NULL,
    `nombre` VARCHAR(150) NOT NULL,
    `activo` BOOLEAN NOT NULL DEFAULT TRUE,
    `creado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `modificado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_carreras_codigo` (`codigo_carrera`),
    KEY `idx_carreras_facultad` (`facultad_id`),
    CONSTRAINT `fk_carreras_facultad`
        FOREIGN KEY (`facultad_id`) REFERENCES `facultades` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE `planes_estudio` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `carrera_id` INT UNSIGNED NOT NULL,
    `codigo_plan` VARCHAR(50) NOT NULL,
    `anio_aprobacion` INT UNSIGNED NOT NULL,
    `activo` BOOLEAN NOT NULL DEFAULT TRUE,
    `creado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `modificado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_plan_carrera_codigo` (`carrera_id`, `codigo_plan`),
    KEY `idx_planes_carrera` (`carrera_id`),
    CONSTRAINT `fk_planes_carrera`
        FOREIGN KEY (`carrera_id`) REFERENCES `carreras` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- NUEVO: creditos_minimos_docente -> creditos que exige la materia al
-- profesor que la va a impartir (varia por materia, a diferencia de la
-- calificacion cuyo umbral es global, ver restricciones).
CREATE TABLE `materias` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `departamento_id` INT UNSIGNED NOT NULL,
    `codigo_materia` VARCHAR(50) NOT NULL,
    `nombre` VARCHAR(150) NOT NULL,
    `creditos` INT UNSIGNED NOT NULL DEFAULT 0,
    `creditos_minimos_docente` INT UNSIGNED NOT NULL DEFAULT 0
        COMMENT 'Creditos minimos del escalafon que debe tener el profesor para impartirla',
    `activo` BOOLEAN NOT NULL DEFAULT TRUE,
    `creado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `modificado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_materias_codigo` (`codigo_materia`),
    KEY `idx_materias_departamento` (`departamento_id`),
    CONSTRAINT `fk_materias_departamento`
        FOREIGN KEY (`departamento_id`) REFERENCES `departamentos` (`id`)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE `detalles_planes` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `plan_estudio_id` INT UNSIGNED NOT NULL,
    `materia_id` INT UNSIGNED NOT NULL,
    `semestre` INT UNSIGNED NOT NULL,
    `anio_carrera` INT UNSIGNED NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_detalles_plan_materia` (`plan_estudio_id`, `materia_id`),
    KEY `idx_detalles_materia` (`materia_id`),
    CONSTRAINT `fk_detalles_plan`
        FOREIGN KEY (`plan_estudio_id`) REFERENCES `planes_estudio` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_detalles_materia`
        FOREIGN KEY (`materia_id`) REFERENCES `materias` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE `grupos` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `carrera_id` INT UNSIGNED NOT NULL,
    `codigo_grupo` VARCHAR(50) NOT NULL,
    `turno` VARCHAR(50) NOT NULL,
    `cantidad_estudiantes` INT UNSIGNED NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_grupos_codigo` (`carrera_id`, `codigo_grupo`),
    KEY `idx_grupos_carrera` (`carrera_id`),
    CONSTRAINT `fk_grupos_carrera`
        FOREIGN KEY (`carrera_id`) REFERENCES `carreras` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE `aulas` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `facultad_id` INT UNSIGNED NOT NULL,
    `nombre` VARCHAR(100) NOT NULL,
    `capacidad` INT UNSIGNED NOT NULL,
    `tipo` VARCHAR(50) NOT NULL COMMENT 'Ej: Teorica, Laboratorio, Auditorio',
    `activo` BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (`id`),
    KEY `idx_aulas_facultad` (`facultad_id`),
    KEY `idx_aulas_tipo_capacidad` (`tipo`, `capacidad`),
    CONSTRAINT `fk_aulas_facultad`
        FOREIGN KEY (`facultad_id`) REFERENCES `facultades` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 2. TIEMPO: PERIODOS Y BLOQUES HORARIOS
-- Catalogo fijo de bloques -> comparaciones por ID en vez de rangos de
-- tiempo, mas rapido para el motor de generacion.
-- ---------------------------------------------------------------------

CREATE TABLE `periodos_academicos` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(50) NOT NULL COMMENT 'Ej: 2026-S1, 2026-Verano',
    `fecha_inicio` DATE NOT NULL,
    `fecha_fin` DATE NOT NULL,
    `activo` BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_periodos_nombre` (`nombre`)
) ENGINE=InnoDB;

CREATE TABLE `bloques_horarios` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(50) NOT NULL COMMENT 'Ej: Bloque-01',
    `hora_inicio` TIME NOT NULL,
    `hora_fin` TIME NOT NULL,
    `orden` INT UNSIGNED NOT NULL COMMENT 'Orden secuencial en el dia, para ordenar UI',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_bloques_horas` (`hora_inicio`, `hora_fin`),
    CHECK (`hora_fin` > `hora_inicio`)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3. DISPONIBILIDAD Y CARGA ACADEMICA
-- ---------------------------------------------------------------------

CREATE TABLE `contratos_profesores` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(100) NOT NULL COMMENT 'Ej: Tiempo completo, Medio tiempo, Por horas',
    `descripcion` VARCHAR(255),
    `horas_max_semanales` INT UNSIGNED NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_contratos_nombre` (`nombre`)
) ENGINE=InnoDB;

-- TABLA PIVOTE: representa "este profesor esta habilitado para dar
-- clases, bajo este contrato, en este periodo". Un solo registro por
-- profesor y periodo. Tanto disponibilidad horaria como carga academica
-- cuelgan de este registro, garantizando que nadie tenga horario ni
-- carga sin un contrato vigente para ese periodo.
CREATE TABLE `disponibilidad_x_profesor` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `profesor_id` INT UNSIGNED NOT NULL,
    `contrato_id` INT UNSIGNED NOT NULL,
    `periodo_academico_id` INT UNSIGNED NOT NULL,
    `activo` BOOLEAN NOT NULL DEFAULT TRUE,
    `creado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_disponibilidad_x_profesor_periodo` (`profesor_id`, `periodo_academico_id`),
    KEY `idx_dxp_contrato` (`contrato_id`),
    CONSTRAINT `fk_dxp_profesor`
        FOREIGN KEY (`profesor_id`) REFERENCES `profesores` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_dxp_contrato`
        FOREIGN KEY (`contrato_id`) REFERENCES `contratos_profesores` (`id`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_dxp_periodo`
        FOREIGN KEY (`periodo_academico_id`) REFERENCES `periodos_academicos` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- Bloques horarios en los que el profesor esta disponible. Cuelga del
-- registro pivote (no de profesor_id directo).
CREATE TABLE `horarios_disponibles` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `disponibilidad_x_profesor_id` INT UNSIGNED NOT NULL,
    `dia` TINYINT UNSIGNED NOT NULL COMMENT '1=Lunes ... 7=Domingo',
    `bloque_id` INT UNSIGNED NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_horarios_disponibles_slot` (`disponibilidad_x_profesor_id`, `dia`, `bloque_id`),
    KEY `idx_horarios_disponibles_busqueda` (`dia`, `bloque_id`, `disponibilidad_x_profesor_id`),
    CONSTRAINT `fk_horariosdisp_dxp`
        FOREIGN KEY (`disponibilidad_x_profesor_id`) REFERENCES `disponibilidad_x_profesor` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_horariosdisp_bloque`
        FOREIGN KEY (`bloque_id`) REFERENCES `bloques_horarios` (`id`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CHECK (`dia` BETWEEN 1 AND 7)
) ENGINE=InnoDB;

-- NUEVO: calificacion del profesor EN una materia especifica, con
-- historial (fecha_evaluacion + vigente). Escala 0.00 - 100.00.
-- El umbral minimo para poder impartir NO vive aqui porque es GLOBAL
-- (mismo valor para todas las materias) -> vive como parametro en
-- `restricciones` (codigo_restriccion = 'calificacion_minima_docente'),
-- igual que los pesos configurables del algoritmo genetico.
CREATE TABLE `calificaciones_docente_materia` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `profesor_id` INT UNSIGNED NOT NULL,
    `materia_id` INT UNSIGNED NOT NULL,
    `calificacion` DECIMAL(5,2) NOT NULL COMMENT 'Escala 0.00 a 100.00',
    `fecha_evaluacion` DATE NOT NULL,
    `evaluado_por` INT UNSIGNED COMMENT 'usuario_id que registro la evaluacion',
    `vigente` BOOLEAN NOT NULL DEFAULT TRUE,
    `creado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_calificaciones_profesor_materia` (`profesor_id`, `materia_id`, `vigente`),
    KEY `idx_calificaciones_materia` (`materia_id`),
    CONSTRAINT `fk_calificaciones_profesor`
        FOREIGN KEY (`profesor_id`) REFERENCES `profesores` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_calificaciones_materia`
        FOREIGN KEY (`materia_id`) REFERENCES `materias` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_calificaciones_usuario`
        FOREIGN KEY (`evaluado_por`) REFERENCES `usuarios` (`id`)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CHECK (`calificacion` BETWEEN 0 AND 100)
) ENGINE=InnoDB;

-- carga_academica = QUE se debe dictar (grupo + materia + profesor + horas),
-- separado de CUANDO/DONDE (horarios_asignados). Un registro de carga
-- academica puede generar varias filas en horarios_asignados
-- (ej: 4 horas/semana repartidas en 2 sesiones de 2 horas).
-- Referencia disponibilidad_x_profesor_id (no profesor_id directo):
-- un profesor sin contrato vigente para el periodo no puede recibir carga.
CREATE TABLE `carga_academica` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `grupo_id` INT UNSIGNED NOT NULL,
    `materia_id` INT UNSIGNED NOT NULL,
    `disponibilidad_x_profesor_id` INT UNSIGNED NOT NULL,
    `periodo_academico_id` INT UNSIGNED NOT NULL,
    `horas_semanales` INT UNSIGNED NOT NULL,
    `creado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_carga_grupo_materia_periodo` (`grupo_id`, `materia_id`, `periodo_academico_id`),
    KEY `idx_carga_dxp_periodo` (`disponibilidad_x_profesor_id`, `periodo_academico_id`),
    CONSTRAINT `fk_carga_grupo`
        FOREIGN KEY (`grupo_id`) REFERENCES `grupos` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_carga_materia`
        FOREIGN KEY (`materia_id`) REFERENCES `materias` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_carga_dxp`
        FOREIGN KEY (`disponibilidad_x_profesor_id`) REFERENCES `disponibilidad_x_profesor` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_carga_periodo`
        FOREIGN KEY (`periodo_academico_id`) REFERENCES `periodos_academicos` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- Nota: periodo_academico_id se repite aqui y en disponibilidad_x_profesor
-- a proposito, por la misma razon que en horarios_asignados: permite el
-- UNIQUE(grupo_id, materia_id, periodo_academico_id) sin JOIN. La
-- aplicacion debe garantizar que ambos coincidan (o se agrega un trigger
-- BEFORE INSERT que lo valide). Es una denormalizacion deliberada por
-- rendimiento, no una redundancia accidental.

-- ---------------------------------------------------------------------
-- 4. MOTOR DE REGLAS
-- Restricciones configurables sin tocar codigo de la aplicacion.
-- Incluye tanto las restricciones del algoritmo genetico (choques de
-- aula/docente/grupo, turno, etc.) como parametros de negocio como el
-- umbral minimo de calificacion docente.
-- ---------------------------------------------------------------------

CREATE TABLE `restricciones` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `codigo_restriccion` VARCHAR(50) NOT NULL,
    `nombre` VARCHAR(150) NOT NULL,
    `descripcion` VARCHAR(255),
    `tipo` ENUM('dura', 'blanda') NOT NULL COMMENT 'dura = obligatoria, blanda = preferencia optimizable',
    `parametros` JSON COMMENT 'Ej: {"max_horas_seguidas": 3} o {"minimo": 70.00}',
    `activo` BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_restricciones_codigo` (`codigo_restriccion`)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 5. GENERACION Y RESULTADO DEL HORARIO
-- ---------------------------------------------------------------------

-- Registro de cada ejecucion del algoritmo generador. Da trazabilidad
-- y es la base para medir KPIs de rendimiento del propio generador.
CREATE TABLE `corridas_generacion` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `periodo_academico_id` INT UNSIGNED NOT NULL,
    `usuario_id` INT UNSIGNED COMMENT 'Quien ejecuto la corrida',
    `algoritmo_usado` VARCHAR(100) NOT NULL,
    `fecha_ejecucion` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `duracion_segundos` DECIMAL(10,2),
    `iteraciones` INT UNSIGNED,
    `estado` ENUM('exitoso', 'parcial', 'fallido') NOT NULL DEFAULT 'parcial',
    `conflictos_detectados` INT UNSIGNED NOT NULL DEFAULT 0,
    `conflictos_resueltos` INT UNSIGNED NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    KEY `idx_corridas_periodo` (`periodo_academico_id`),
    CONSTRAINT `fk_corridas_periodo`
        FOREIGN KEY (`periodo_academico_id`) REFERENCES `periodos_academicos` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_corridas_usuario`
        FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- Resultado final: CUANDO y DONDE ocurre cada carga academica.
-- periodo_academico_id esta denormalizado aqui a proposito: permite
-- constraints UNIQUE compuestos que la base de datos valida sola.
CREATE TABLE `horarios_asignados` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `carga_academica_id` INT UNSIGNED NOT NULL,
    `aula_id` INT UNSIGNED NOT NULL,
    `periodo_academico_id` INT UNSIGNED NOT NULL,
    `corrida_generacion_id` INT UNSIGNED,
    `dia` TINYINT UNSIGNED NOT NULL COMMENT '1=Lunes ... 7=Domingo',
    `bloque_id` INT UNSIGNED NOT NULL,
    `estado` ENUM('borrador', 'publicado', 'archivado') NOT NULL DEFAULT 'borrador',
    `creado` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    -- Un aula no puede tener 2 clases en el mismo dia/bloque/periodo
    UNIQUE KEY `uq_horario_aula_slot` (`aula_id`, `periodo_academico_id`, `dia`, `bloque_id`),
    KEY `idx_horario_carga` (`carga_academica_id`),
    KEY `idx_horario_periodo_estado` (`periodo_academico_id`, `estado`),
    KEY `idx_horario_corrida` (`corrida_generacion_id`),
    CONSTRAINT `fk_horario_carga`
        FOREIGN KEY (`carga_academica_id`) REFERENCES `carga_academica` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_horario_aula`
        FOREIGN KEY (`aula_id`) REFERENCES `aulas` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_horario_periodo`
        FOREIGN KEY (`periodo_academico_id`) REFERENCES `periodos_academicos` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_horario_bloque`
        FOREIGN KEY (`bloque_id`) REFERENCES `bloques_horarios` (`id`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_horario_corrida`
        FOREIGN KEY (`corrida_generacion_id`) REFERENCES `corridas_generacion` (`id`)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CHECK (`dia` BETWEEN 1 AND 7)
) ENGINE=InnoDB;

-- Nota de diseno: la validacion de que un PROFESOR o un GRUPO no
-- choquen (a diferencia del aula, que ya esta protegida por la unica
-- de arriba) requiere cruzar horarios_asignados -> carga_academica.
-- Se recomienda una vista materializada o trigger BEFORE INSERT que
-- valide esto contra carga_academica.disponibilidad_x_profesor_id
-- (que resuelve al profesor) y carga_academica.grupo_id antes de
-- insertar.

-- ---------------------------------------------------------------------
-- 6. METRICAS KPI (enfocadas en calidad de horarios, no en TI)
-- ---------------------------------------------------------------------

CREATE TABLE `metricas_kpi` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `codigo_kpi` VARCHAR(30) NOT NULL,
    `nombre_kpi` VARCHAR(100) NOT NULL,
    `descripcion` VARCHAR(255) NOT NULL,
    `unidad_medida` VARCHAR(20) NOT NULL DEFAULT 'Porcentaje',
    `umbral_advertencia` DECIMAL(5,2) NOT NULL,
    `umbral_critico` DECIMAL(5,2) NOT NULL,
    `activo` BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_metricas_codigo` (`codigo_kpi`),
    UNIQUE KEY `uq_metricas_nombre` (`nombre_kpi`)
) ENGINE=InnoDB;

-- Tabla de hechos: cada medicion de un KPI, a nivel global o de una
-- entidad especifica (profesor, aula, departamento, grupo).
CREATE TABLE `mediciones_kpi` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `metrica_kpi_id` INT UNSIGNED NOT NULL,
    `corrida_generacion_id` INT UNSIGNED,
    `periodo_academico_id` INT UNSIGNED NOT NULL,
    `entidad_tipo` ENUM('profesor', 'aula', 'departamento', 'grupo', 'global') NOT NULL DEFAULT 'global',
    `entidad_id` INT UNSIGNED COMMENT 'NULL cuando entidad_tipo = global',
    `valor_registrado` DECIMAL(10,2) NOT NULL,
    `fecha_medicion` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_mediciones_metrica_periodo` (`metrica_kpi_id`, `periodo_academico_id`),
    KEY `idx_mediciones_entidad` (`entidad_tipo`, `entidad_id`),
    KEY `idx_mediciones_corrida` (`corrida_generacion_id`),
    CONSTRAINT `fk_mediciones_metrica`
        FOREIGN KEY (`metrica_kpi_id`) REFERENCES `metricas_kpi` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_mediciones_corrida`
        FOREIGN KEY (`corrida_generacion_id`) REFERENCES `corridas_generacion` (`id`)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_mediciones_periodo`
        FOREIGN KEY (`periodo_academico_id`) REFERENCES `periodos_academicos` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- =====================================================================
-- FIN DEL SCRIPT
-- =====================================================================

SET FOREIGN_KEY_CHECKS = 1;
