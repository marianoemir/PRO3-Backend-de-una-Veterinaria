-- Caso C-08: UPDATE directo en la base
-- Precondición: python reiniciar.py
-- Ejecutar en el Query Tool de pgAdmin (base veterinaria) o con psql: psql -U postgres -d veterinaria -f test/caso_C-08.sql
UPDATE practica SET precio = 0 WHERE id = 1;
-- Esperado: ERROR: new row for relation "practica" violates check constraint "ck_practica_precio_positivo" (SQLSTATE 23514); 0 filas modificadas.
-- Opcional:
-- UPDATE practica SET precio = -1 WHERE id = 1;
