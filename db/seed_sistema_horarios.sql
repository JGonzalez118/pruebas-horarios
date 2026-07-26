-- =====================================================================
-- SEED DE DATOS DE PRUEBA — API de pruebas del Algoritmo Genético
-- Basado (de forma ficticia) en la Facultad de Ingeniería de Sistemas
-- Computacionales (FISC) de la Universidad Tecnológica de Panamá.
-- Nombres de profesores, cédulas, correos y horarios son inventados
-- únicamente para practicar el GA. Ejecutar DESPUÉS del script
-- Sistema_de_Gestion_de_Horarios_v4_FINAL.sql
-- =====================================================================

USE `sistema_horarios_ga`;
SET FOREIGN_KEY_CHECKS = 0;

-- NOTA: este seed asume que ya corriste antes
-- sistema_horarios_ga_completo.sql (schema completo con creditos +
-- calificaciones ya integrados desde la definicion de las tablas).

-- ---------------------------------------------------------------------
-- 1. ROLES Y FACULTAD
-- ---------------------------------------------------------------------

INSERT INTO `roles` (`id`, `nombre_rol`, `descripcion`) VALUES
(1, 'Administrador', 'Acceso total al sistema'),
(2, 'Coordinador Académico', 'Gestiona horarios y carga académica de su facultad');

INSERT INTO `facultades` (`id`, `codigo_facultad`, `nombre`) VALUES
(1, 'FISC', 'Facultad de Ingeniería de Sistemas Computacionales');

INSERT INTO `departamentos` (`id`, `facultad_id`, `nombre`, `descripcion`) VALUES
(1, 1, 'Departamento de Ingeniería de Software', 'Programación, arquitectura y desarrollo de software'),
(2, 1, 'Departamento de Sistemas de Información', 'Bases de datos, redes e infraestructura'),
(3, 1, 'Departamento de Ciencias Básicas de la Computación', 'Matemática, algoritmos y fundamentos');

INSERT INTO `usuarios`
(`id`, `rol_id`, `departamento_id`, `cedula`, `nombre`, `apellido`, `correo`, `password_hash`)
VALUES
(1, 2, 1, '8-888-0001', 'Ana', 'Rodríguez', 'coord.fisc@utp.test', '$2y$10$fakehashfakehashfakehashfa');

-- ---------------------------------------------------------------------
-- 2. CARRERAS Y PLANES DE ESTUDIO (nombres reales de la oferta de FISC)
-- ---------------------------------------------------------------------

INSERT INTO `carreras` (`id`, `facultad_id`, `codigo_carrera`, `nombre`) VALUES
(1, 1, 'LISC', 'Licenciatura en Ingeniería de Sistemas y Computación'),
(2, 1, 'LIS',  'Licenciatura en Ingeniería de Software'),
(3, 1, 'LCIB', 'Licenciatura en Ciberseguridad');

INSERT INTO `planes_estudio` (`id`, `carrera_id`, `codigo_plan`, `anio_aprobacion`) VALUES
(1, 1, 'LISC-2022', 2022),
(2, 2, 'LIS-2022', 2022),
(3, 3, 'LCIB-2023', 2023);

-- ---------------------------------------------------------------------
-- 3. MATERIAS (genéricas, típicas de un plan de sistemas)
-- ---------------------------------------------------------------------

-- creditos_minimos_docente: créditos del escalafón que exige la materia
-- (materias más avanzadas exigen más créditos del profesor que la dicta)
INSERT INTO `materias` (`id`, `departamento_id`, `codigo_materia`, `nombre`, `creditos`, `creditos_minimos_docente`) VALUES
(1,  3, 'MAT-101', 'Cálculo I', 4, 20),
(2,  3, 'ALG-101', 'Algoritmos y Estructuras de Datos', 4, 20),
(3,  1, 'PRG-101', 'Programación I', 4, 10),
(4,  1, 'PRG-102', 'Programación II', 4, 15),
(5,  2, 'BDD-201', 'Bases de Datos I', 3, 20),
(6,  2, 'RED-201', 'Redes de Computadoras', 3, 20),
(7,  1, 'ISW-201', 'Ingeniería de Software I', 3, 25),
(8,  2, 'SOP-201', 'Sistemas Operativos', 3, 25),
(9,  3, 'MAT-201', 'Matemática Discreta', 3, 15),
(10, 1, 'ISW-301', 'Arquitectura de Software', 3, 30),
(11, 2, 'SEG-301', 'Fundamentos de Ciberseguridad', 3, 25),
(12, 3, 'ING-101', 'Inglés Técnico I', 2, 5);

-- Detalle de plan: qué materias corresponden a qué semestre de cada plan
INSERT INTO `detalles_planes` (`plan_estudio_id`, `materia_id`, `semestre`, `anio_carrera`) VALUES
(1, 1, 1, 1), (1, 3, 1, 1), (1, 12, 1, 1),
(1, 2, 2, 1), (1, 4, 2, 1), (1, 9, 2, 1),
(1, 5, 3, 2), (1, 6, 3, 2), (1, 7, 3, 2),
(2, 3, 1, 1), (2, 1, 1, 1),
(2, 4, 2, 1), (2, 7, 2, 1),
(2, 10, 3, 2), (2, 5, 3, 2),
(3, 3, 1, 1), (3, 9, 1, 1),
(3, 6, 2, 1), (3, 8, 2, 1),
(3, 11, 3, 2);

-- ---------------------------------------------------------------------
-- 4. GRUPOS (mezcla de turnos, para probar la restricción de turno)
-- ---------------------------------------------------------------------

INSERT INTO `grupos` (`id`, `carrera_id`, `codigo_grupo`, `turno`, `cantidad_estudiantes`) VALUES
(1, 1, 'LISC-1A-M', 'matutino',   35),
(2, 1, 'LISC-2A-M', 'matutino',   32),
(3, 1, 'LISC-3A-V', 'vespertino', 28),
(4, 2, 'LIS-1A-M',  'matutino',   30),
(5, 2, 'LIS-2A-N',  'nocturno',   25),
(6, 3, 'LCIB-1A-V', 'vespertino', 27);

-- ---------------------------------------------------------------------
-- 5. AULAS (compartidas por toda la facultad)
-- ---------------------------------------------------------------------

INSERT INTO `aulas` (`id`, `facultad_id`, `nombre`, `capacidad`, `tipo`) VALUES
(1, 1, 'Aula 301', 40, 'Teorica'),
(2, 1, 'Aula 302', 40, 'Teorica'),
(3, 1, 'Aula 303', 35, 'Teorica'),
(4, 1, 'Lab. Redes 1',      25, 'Laboratorio'),
(5, 1, 'Lab. Programacion 1', 30, 'Laboratorio'),
(6, 1, 'Auditorio FISC',    80, 'Auditorio');

-- ---------------------------------------------------------------------
-- 6. PERIODO ACADÉMICO Y BLOQUES HORARIOS (7:00 a 22:00, bloques de 1h)
-- ---------------------------------------------------------------------

INSERT INTO `periodos_academicos` (`id`, `nombre`, `fecha_inicio`, `fecha_fin`, `activo`) VALUES
(1, '2026-S1', '2026-08-03', '2026-12-11', TRUE);

INSERT INTO `bloques_horarios` (`id`, `nombre`, `hora_inicio`, `hora_fin`, `orden`) VALUES
(1,  'Bloque-01', '07:00:00', '08:00:00', 1),
(2,  'Bloque-02', '08:00:00', '09:00:00', 2),
(3,  'Bloque-03', '09:00:00', '10:00:00', 3),
(4,  'Bloque-04', '10:00:00', '11:00:00', 4),
(5,  'Bloque-05', '11:00:00', '12:00:00', 5),
(6,  'Bloque-06', '13:00:00', '14:00:00', 6),
(7,  'Bloque-07', '14:00:00', '15:00:00', 7),
(8,  'Bloque-08', '15:00:00', '16:00:00', 8),
(9,  'Bloque-09', '16:00:00', '17:00:00', 9),
(10, 'Bloque-10', '17:00:00', '18:00:00', 10),
(11, 'Bloque-11', '18:00:00', '19:00:00', 11),
(12, 'Bloque-12', '19:00:00', '20:00:00', 12),
(13, 'Bloque-13', '20:00:00', '21:00:00', 13),
(14, 'Bloque-14', '21:00:00', '22:00:00', 14);

-- ---------------------------------------------------------------------
-- 7. CONTRATOS Y PROFESORES
-- ---------------------------------------------------------------------

INSERT INTO `contratos_profesores` (`id`, `nombre`, `descripcion`, `horas_max_semanales`) VALUES
(1, 'Tiempo completo', 'Dedicación exclusiva, horario 9:00-20:00', 20),
(2, 'Medio tiempo',    'Dedicación parcial', 12),
(3, 'Por horas',       'Contrato por asignatura', 8);

-- creditos_academicos: créditos del escalafón docente de cada profesor
INSERT INTO `profesores` (`id`, `departamento_id`, `cedula`, `nombre`, `apellido`, `correo`, `creditos_academicos`) VALUES
(1, 1, '8-101-0001', 'Carlos', 'Gómez',    'cgomez@fisc.test',    18),  -- tiempo completo, veterano en PRG
(2, 1, '8-101-0002', 'María',  'Herrera',  'mherrera@fisc.test',  28),  -- medio tiempo, alta especialización ISW
(3, 2, '8-101-0003', 'Luis',   'Batista',  'lbatista@fisc.test',  25),  -- tiempo completo
(4, 2, '8-101-0004', 'Yariela','Pinzón',   'ypinzon@fisc.test',   22),  -- por horas, redes
(5, 3, '8-101-0005', 'Roberto','Sánchez',  'rsanchez@fisc.test',  20),  -- tiempo completo, matemática
(6, 3, '8-101-0006', 'Diana',  'Castillo', 'dcastillo@fisc.test', 24),  -- medio tiempo, algoritmos
(7, 1, '8-101-0007', 'Jorge',  'Núñez',    'jnunez@fisc.test',    30),  -- por horas, alta experiencia ISW
(8, 2, '8-101-0008', 'Katia',  'Rovira',   'krovira@fisc.test',    8);  -- medio tiempo, solo inglés técnico

-- ---------------------------------------------------------------------
-- 8. DISPONIBILIDAD POR PROFESOR (contrato vigente para 2026-S1)
-- ---------------------------------------------------------------------

INSERT INTO `disponibilidad_x_profesor` (`id`, `profesor_id`, `contrato_id`, `periodo_academico_id`) VALUES
(1, 1, 1, 1),  -- Carlos Gómez, tiempo completo
(2, 2, 2, 1),  -- María Herrera, medio tiempo
(3, 3, 1, 1),  -- Luis Batista, tiempo completo
(4, 4, 3, 1),  -- Yariela Pinzón, por horas
(5, 5, 1, 1),  -- Roberto Sánchez, tiempo completo
(6, 6, 2, 1),  -- Diana Castillo, medio tiempo
(7, 7, 3, 1),  -- Jorge Núñez, por horas
(8, 8, 2, 1);  -- Katia Rovira, medio tiempo

-- Disponibilidad horaria: día 1=Lunes ... 5=Viernes
-- Tiempo completo (Carlos, Luis, Roberto): disponibles 9:00-20:00 (bloques 3-13), L-V
INSERT INTO `horarios_disponibles` (`disponibilidad_x_profesor_id`, `dia`, `bloque_id`)
SELECT dxp.id, dia.n, bloque.id
FROM (SELECT 1 AS id UNION SELECT 3 UNION SELECT 5) AS dxp
CROSS JOIN (SELECT 1 AS n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) AS dia
CROSS JOIN `bloques_horarios` AS bloque
WHERE bloque.orden BETWEEN 3 AND 13;

-- Medio tiempo (María, Diana, Katia): disponibles todo el día, L-V
INSERT INTO `horarios_disponibles` (`disponibilidad_x_profesor_id`, `dia`, `bloque_id`)
SELECT dxp.id, dia.n, bloque.id
FROM (SELECT 2 AS id UNION SELECT 6 UNION SELECT 8) AS dxp
CROSS JOIN (SELECT 1 AS n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) AS dia
CROSS JOIN `bloques_horarios` AS bloque;

-- Por horas (Yariela, Jorge): solo disponibles en las tardes/noches, L-V
INSERT INTO `horarios_disponibles` (`disponibilidad_x_profesor_id`, `dia`, `bloque_id`)
SELECT dxp.id, dia.n, bloque.id
FROM (SELECT 4 AS id UNION SELECT 7) AS dxp
CROSS JOIN (SELECT 1 AS n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) AS dia
CROSS JOIN `bloques_horarios` AS bloque
WHERE bloque.orden BETWEEN 6 AND 14;

-- ---------------------------------------------------------------------
-- 9. CARGA ACADÉMICA (grupo + materia + profesor ya asignado + horas)
--    Esto simula lo que el coordinador ya habría decidido manualmente.
-- ---------------------------------------------------------------------

INSERT INTO `carga_academica`
(`grupo_id`, `materia_id`, `disponibilidad_x_profesor_id`, `periodo_academico_id`, `horas_semanales`)
VALUES
-- LISC-1A-M (grupo 1)
(1, 1,  5, 1, 4),  -- Cálculo I → Roberto Sánchez
(1, 3,  1, 1, 4),  -- Programación I → Carlos Gómez
(1, 12, 8, 1, 2),  -- Inglés Técnico I → Katia Rovira

-- LISC-2A-M (grupo 2)
(2, 2,  6, 1, 4),  -- Algoritmos y Estructuras de Datos → Diana Castillo
(2, 4,  1, 1, 4),  -- Programación II → Carlos Gómez
(2, 9,  5, 1, 3),  -- Matemática Discreta → Roberto Sánchez

-- LISC-3A-V (grupo 3, vespertino)
(3, 5,  3, 1, 3),  -- Bases de Datos I → Luis Batista
(3, 6,  4, 1, 3),  -- Redes de Computadoras → Yariela Pinzón
(3, 7,  2, 1, 3),  -- Ingeniería de Software I → María Herrera

-- LIS-1A-M (grupo 4)
(4, 3,  1, 1, 4),  -- Programación I → Carlos Gómez
(4, 1,  5, 1, 4),  -- Cálculo I → Roberto Sánchez

-- LIS-2A-N (grupo 5, nocturno)
(5, 7,  7, 1, 3),  -- Ingeniería de Software I → Jorge Núñez
(5, 10, 2, 1, 3),  -- Arquitectura de Software → María Herrera

-- LCIB-1A-V (grupo 6, vespertino)
(6, 6,  4, 1, 3),  -- Redes de Computadoras → Yariela Pinzón
(6, 8,  3, 1, 3);  -- Sistemas Operativos → Luis Batista

-- ---------------------------------------------------------------------
-- 9.5 CALIFICACIONES DOCENTE-MATERIA (con historial)
--     Escala 0-100. Umbral mínimo global (70) vive en `restricciones`,
--     insertado por 02_extension_creditos_calificaciones.sql
--     Todas las asignaciones de carga_academica de arriba corresponden
--     a profesores que SÍ califican (>= 70), excepto un par de filas
--     de ejemplo con calificación baja para probar que el filtro de
--     elegibilidad los excluye correctamente.
-- ---------------------------------------------------------------------

INSERT INTO `calificaciones_docente_materia`
(`profesor_id`, `materia_id`, `calificacion`, `fecha_evaluacion`, `evaluado_por`, `vigente`) VALUES
-- Carlos Gómez → Programación I y II (su fuerte)
(1, 3,  92.50, '2025-06-15', 1, TRUE),
(1, 4,  88.00, '2025-06-15', 1, TRUE),

-- María Herrera → Ingeniería de Software I y Arquitectura de Software
(2, 7,  95.00, '2025-06-15', 1, TRUE),
(2, 10, 90.00, '2025-06-15', 1, TRUE),

-- Luis Batista → Bases de Datos I y Sistemas Operativos
(3, 5,  85.00, '2025-06-15', 1, TRUE),
(3, 8,  78.00, '2025-06-15', 1, TRUE),

-- Yariela Pinzón → Redes de Computadoras
(4, 6,  91.00, '2025-06-15', 1, TRUE),

-- Roberto Sánchez → Cálculo I y Matemática Discreta
(5, 1,  89.00, '2025-06-15', 1, TRUE),
(5, 9,  84.00, '2025-06-15', 1, TRUE),

-- Diana Castillo → Algoritmos y Estructuras de Datos
(6, 2,  93.00, '2025-06-15', 1, TRUE),

-- Jorge Núñez → Ingeniería de Software I (segunda opción, buena nota igual)
(7, 7,  87.00, '2025-06-15', 1, TRUE),

-- Katia Rovira → Inglés Técnico I
(8, 12, 96.00, '2025-06-15', 1, TRUE),

-- --- Ejemplos de calificación INSUFICIENTE (< 70), para probar el filtro ---
-- Katia Rovira intentó una vez dar Redes de Computadoras, pero no calificó
(8, 6,  62.00, '2024-01-20', 1, FALSE),  -- evaluación antigua, ya no vigente
-- Yariela Pinzón fue evaluada en Sistemas Operativos y no alcanzó el mínimo
(4, 8,  65.00, '2025-06-15', 1, TRUE);   -- vigente pero por debajo del umbral

-- ---------------------------------------------------------------------
-- 10. RESTRICCIONES (motor de reglas configurable)
-- ---------------------------------------------------------------------

INSERT INTO `restricciones`
(`codigo_restriccion`, `nombre`, `descripcion`, `tipo`, `parametros`, `activo`) VALUES
('aula_duplicada', 'Aula sin choques', 'Un aula no puede tener 2 grupos al mismo tiempo', 'dura',
    JSON_OBJECT('peso', 1000), TRUE),
('docente_duplicado', 'Docente sin choques', 'Un docente no puede dar 2 clases al mismo tiempo', 'dura',
    JSON_OBJECT('peso', 1000), TRUE),
('grupo_dos_clases', 'Grupo sin choques', 'Un grupo no puede tener 2 clases al mismo tiempo', 'dura',
    JSON_OBJECT('peso', 1000), TRUE),
('profesor_no_disponible', 'Respeta disponibilidad', 'Solo usar bloques declarados por el profesor', 'dura',
    JSON_OBJECT('peso', 1000), TRUE),
('turno_correcto', 'Horario según turno del grupo', 'Matutino 7-12, vespertino 13-18, nocturno 17-22', 'blanda',
    JSON_OBJECT('peso', 200), TRUE),
('horas_equilibradas', 'Carga diaria equilibrada', 'Distribuir horas de forma pareja entre días', 'blanda',
    JSON_OBJECT('peso', 50), TRUE),
('clases_corridas', 'Horario sin huecos', 'Evitar espacios vacíos entre clases del mismo grupo', 'blanda',
    JSON_OBJECT('peso', 100), TRUE);

SET FOREIGN_KEY_CHECKS = 1;[]

-- =====================================================================
-- FIN DEL SEED
-- =====================================================================
