from database import db
import hashlib

class Auth:
    def __init__(self):
        self.current_user = None
        self.current_turno = None

    def login(self, username, password):
        query = """
        SELECT id, nombre, username, tipo 
        FROM usuarios 
        WHERE username = %s AND password = %s AND activo = 1
        """
        user = db.execute_one(query, (username, password))
        
        if user:
            self.current_user = user
            # Si es cajero, verificar si tiene turno abierto
            if user['tipo'] == 'cajero':
                self.check_turno_abierto()
            return True
        return False

    def check_turno_abierto(self):
        query = """
        SELECT * FROM turnos 
        WHERE cajero_id = %s AND estado = 'abierto'
        ORDER BY fecha_inicio DESC 
        LIMIT 1
        """
        turno = db.execute_one(query, (self.current_user['id'],))
        if turno:
            self.current_turno = turno

    def logout(self):
        self.current_user = None
        self.current_turno = None

    def is_authenticated(self):
        return self.current_user is not None

    def has_permission(self, required_type):
        if not self.current_user:
            return False
        
        user_type = self.current_user['tipo']
        
        if required_type == 'cajero':
            return user_type in ['cajero', 'administrador', 'superusuario']
        elif required_type == 'administrador':
            return user_type in ['administrador', 'superusuario']
        elif required_type == 'superusuario':
            return user_type == 'superusuario'
        
        return False

    def crear_turno(self, fondo_inicial):
        if not self.current_user or self.current_user['tipo'] != 'cajero':
            return False
        
        # Verificar que no tenga turno abierto
        if self.current_turno:
            return False
        
        query = """
        INSERT INTO turnos (cajero_id, fondo_inicial, fecha_inicio)
        VALUES (%s, %s, NOW())
        """
        turno_id = db.execute_one(query, (self.current_user['id'], fondo_inicial))
        
        if turno_id:
            # Cargar el turno creado
            query = "SELECT * FROM turnos WHERE id = %s"
            self.current_turno = db.execute_one(query, (turno_id,))
            return True
        
        return False

    def cerrar_turno(self, efectivo_final, tarjeta_final):
        if not self.current_turno:
            print("ERROR: No hay turno activo para cerrar")
            return False
        
        try:
            print(f"DEBUG: Cerrando turno {self.current_turno['id']}")
            print(f"DEBUG: Efectivo final: {efectivo_final}, Tarjeta final: {tarjeta_final}")
            
            # Calcular total de ventas del turno
            query = """
            SELECT COALESCE(SUM(total), 0) as total_ventas
            FROM ordenes 
            WHERE turno_id = %s
            """
            result = db.execute_one(query, (self.current_turno['id'],))
            
            # Convertir a float para evitar problemas de tipo
            total_ventas = float(result['total_ventas']) if result else 0.0
            fondo_inicial = float(self.current_turno['fondo_inicial'])
            
            print(f"DEBUG: Total ventas: {total_ventas}, Fondo inicial: {fondo_inicial}")
            
            # Calcular faltante - todos los valores como float
            total_esperado = fondo_inicial + total_ventas
            total_real = float(efectivo_final) + float(tarjeta_final)
            faltante = total_esperado - total_real
            
            print(f"DEBUG: Total esperado: {total_esperado}, Total real: {total_real}, Faltante: {faltante}")
            
            # Cerrar turno
            query = """
            UPDATE turnos 
            SET fecha_cierre = NOW(), efectivo_final = %s, tarjeta_final = %s,
                total_ventas = %s, faltante = %s, estado = 'cerrado'
            WHERE id = %s
            """
            result = db.execute_query(query, (
                float(efectivo_final), float(tarjeta_final), total_ventas, faltante, self.current_turno['id']
            ))
            
            print(f"DEBUG: Resultado actualización: {result}")
            
            if result:
                print("DEBUG: Turno cerrado exitosamente")
                self.current_turno = None
                return True
            else:
                print("ERROR: No se pudo actualizar el turno en la base de datos")
                return False
                
        except Exception as e:
            print(f"ERROR en cerrar_turno: {e}")
            return False

# Instancia global de autenticación
auth = Auth()
