import mysql.connector
from mysql.connector import Error

# Configuración de conexión a MySQL (usar credenciales adecuadas)
config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'billetera_digital'
}

def get_connection():
    try:
        connection = mysql.connector.connect(**config)
        return connection
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

def init_database():
    # Primero intentamos conectar sin especificar la base para poder crearla si falta
    config_no_db = {k: v for k, v in config.items() if k != 'database'}
    try:
        conn = mysql.connector.connect(**config_no_db)
    except Error as e:
        print(f"Error al conectar al servidor MySQL para inicializar DB: {e}")
        return

    cursor = conn.cursor()
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS sistema CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
    except Error as e:
        print(f"Error al crear la base de datos 'sistema': {e}")
        cursor.close()
        conn.close()
        return
    finally:
        cursor.close()
        conn.close()

    # Ahora conectamos a la base de datos creada y creamos tablas
    connection = get_connection()
    if not connection:
        print("No se pudo conectar a la base de datos 'sistema' después de crearla")
        return

    cursor = connection.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id_usuario INT AUTO_INCREMENT PRIMARY KEY,
                usuario VARCHAR(50) UNIQUE,
                password VARCHAR(255),
                rol ENUM('admin','usuario'),
                estado TINYINT(1),
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id_categoria INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100),
                descripcion VARCHAR(255),
                estado TINYINT(1),
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id_producto INT AUTO_INCREMENT PRIMARY KEY,
                id_categoria INT,
                nombre VARCHAR(150),
                descripcion VARCHAR(255),
                precio DECIMAL(10,2),
                stock INT,
                estado TINYINT(1),
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cliente (
                id_cliente INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100),
                apellido VARCHAR(100),
                dni VARCHAR(15),
                telefono VARCHAR(20),
                correo VARCHAR(100),
                direccion VARCHAR(200),
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id_venta INT AUTO_INCREMENT PRIMARY KEY,
                id_cliente INT,
                id_usuario INT,
                fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total DECIMAL(10,2)
            )
        """)
        # insertar admin por defecto si no existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO usuarios (usuario, password, rol, estado) 
                VALUES ('admin', 'admin123', 'admin', 1)
            """)
        connection.commit()
        print("Base de datos inicializada correctamente")
    except Error as e:
        print(f"Error al crear tablas: {e}")
    finally:
        cursor.close()
        connection.close()