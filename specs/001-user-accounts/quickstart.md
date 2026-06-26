# Quickstart — Verificar la Fase 1 (cuentas)

Una vez implementado, validar así:

1. **Registro:** crear cuenta con email+password nuevos → recibe token, queda logueado.
2. **Email duplicado:** intentar registrar el mismo email → rechazado (409).
3. **Login:** cerrar sesión, entrar con credenciales correctas → ok; con incorrectas → 401 genérico.
4. **Persistencia:** logueado, subir un documento; cerrar sesión; volver a entrar → el documento sigue disponible.
5. **Aislamiento:** con usuario B, consultar → NO ve los documentos del usuario A; sí ve los de demo.
6. **Modo anónimo:** sin cuenta, subir y consultar → funciona igual que antes (aislado por sesión, efímero).
7. **Eliminar cuenta:** borrar cuenta → sus documentos desaparecen.

Tests automatizados (pytest) deben cubrir 1, 3, 4, 5 y 6.
