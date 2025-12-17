from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_connection, init_database
from werkzeug.security import check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'cambia_esta_clave_en_produccion')

# Inicializar (si tienes esta función en database.py)
init_database()

def requiere_login(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorador

def is_hashed(s: str) -> bool:
    if not s or not isinstance(s, str):
        return False
    s_lower = s.lower()
    return s_lower.startswith('pbkdf2:') or s_lower.startswith('scrypt:') \
           or s_lower.startswith('argon2') or s_lower.startswith('$2') or s_lower.startswith('bcrypt')

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = (request.form.get('usuario') or request.form.get('username') or '').strip()
        password = (request.form.get('password') or '').strip()

        if not usuario or not password:
            flash('Por favor ingresa usuario y contraseña', 'warning')
            return render_template('login.html')

        conn = get_connection()
        if conn is None:
            flash('No se pudo conectar a la base de datos', 'danger')
            return render_template('login.html')

        try:
            cur = conn.cursor(dictionary=True)
            # Aseguramos que buscamos usuarios con estado ACTIVO (case-insensitive)
            cur.execute("SELECT * FROM usuarios WHERE username = %s AND UPPER(estado) = 'ACTIVO'", (usuario,))
            user = cur.fetchone()
        except Exception as e:
            # Imprime la excepción en la consola para depuración y devuelve el formulario
            print("EXCEPCIÓN en consulta login:", e)
            flash('Error de servidor al intentar iniciar sesión', 'danger')
            # cierre seguro antes de retornar
            try:
                cur.close()
            except:
                pass
            try:
                conn.close()
            except:
                pass
            # retornamos aquí para evitar seguir con la lógica y agregar otro flash
            return render_template('login.html')
        finally:
            # Si no hubo excepción, cur y conn se cerrarán aquí (si existen)
            # Nota: si ya cerramos en el except, los try/except evitan error
            try:
                cur.close()
            except:
                pass
            try:
                conn.close()
            except:
                pass

        if not user:
            flash('Usuario o contraseña incorrectos', 'warning')
            return render_template('login.html')

        stored = user.get('password_hash') or user.get('password') or ''
        verified = False

        if is_hashed(stored):
            try:
                verified = check_password_hash(stored, password)
            except Exception as e:
                print("Error verificando hash:", e)
                flash('Error verificando la contraseña (formato de hash incompatible)', 'danger')
                return render_template('login.html')
        else:
            verified = (stored == password)

        if verified:
            session['usuario'] = user.get('username') or user.get('usuario')
            session['id_usuario'] = user.get('id_usuario')
            session['rol'] = user.get('rol') or user.get('role')
            flash(f'Bienvenido {session["usuario"]}', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'warning')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@requiere_login
def dashboard():
    conn = get_connection()
    usuarios = cuentas = transacciones = []
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id_usuario, username, estado, fecha_creacion, rol FROM usuarios ORDER BY id_usuario DESC")
            usuarios = cur.fetchall()
            cur.execute("SELECT id_cuenta, id_usuario, saldo, moneda, estado FROM cuentas ORDER BY id_cuenta DESC")
            cuentas = cur.fetchall()
            cur.execute("SELECT id_transaccion, id_cuenta, tipo_movimiento, monto, fecha, estado FROM transacciones ORDER BY id_transaccion DESC")
            transacciones = cur.fetchall()
        except Exception as e:
            print("Error cargando datos dashboard:", e)
            flash('Error al obtener datos de la base de datos', 'danger')
        finally:
            try:
                cur.close()
            except:
                pass
            try:
                conn.close()
            except:
                pass

    return render_template('dashboard.html', usuarios=usuarios, cuentas=cuentas, transacciones=transacciones)

if __name__ == '__main__':
    app.run(debug=True)