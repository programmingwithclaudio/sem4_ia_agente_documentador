### Empoints

```bash
curl -X POST http://localhost:8000/api/auth/signup ^
-H "Content-Type: application/json" ^
-d "{\"username\": \"admin1\", \"email\": \"admin1@example.com\", \"password\": \"adminpass123\", \"roles\": [\"ROLE_ADMIN\"]}"

```

```bash
curl -X POST http://localhost:8000/api/auth/signin  ^
-H "Content-Type: application/json" ^
-d "{\"username\": \"admin2\", \"password\": \"adminpass123\"}"

curl -X POST http://localhost:8000/api/auth/signin ^
-H "Content-Type: application/x-www-form-urlencoded" ^
-d "username=admin2&password=adminpass123"
```

- ok admin2 cokkies

curl -X POST http://localhost:5000/api/auth/signout ^
-H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczMjQ3OTMwOSwianRpIjoiYWY1MDJkZDEtNmQyNS00NDQ4LWIwMGEtYTU5M2E3ZGUyYzRjIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3MzI0NzkzMDksImNzcmYiOiJmYmIyMjc1MC0yYWNiLTQ1YTctYWQ1Ny1kY2YwZTUzMDAwOTMiLCJleHAiOjE3MzI1NjU3MDl9.8VS3vdX87u_gBtg0OGSyISuD1XHx20sRyJMfof126i4"

- ok admin2 cokkies
curl -X GET http://localhost:5000/api/users ^
-H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczMjQ3OTMwOSwianRpIjoiYWY1MDJkZDEtNmQyNS00NDQ4LWIwMGEtYTU5M2E3ZGUyYzRjIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3MzI0NzkzMDksImNzcmYiOiJmYmIyMjc1MC0yYWNiLTQ1YTctYWQ1Ny1kY2YwZTUzMDAwOTMiLCJleHAiOjE3MzI1NjU3MDl9.8VS3vdX87u_gBtg0OGSyISuD1XHx20sRyJMfof126i4" ^
-H "Content-Type: application/json"

---



---

#### Errores 
- La biblioteca json no sabe cómo manejar este tipo de objeto, y por ello se genera la excepción TypeError: Object of type timedelta is not JSON serializable.

Para solucionar esto, debes convertir el objeto timedelta a un valor que pueda ser serializado, como el número de segundos, minutos u horas. Te sugeriría modificar la forma en que estableces el campo exp en el token JWT.

- En tu implementación de FastAPI, estás tratando de crear una lógica para el manejo de autenticación utilizando cookies y JWT, similar a la que se realiza en Flask. Sin embargo, parece que hay una confusión respecto al manejo de cookies y la estructura de la respuesta para enviar el token JWT. A continuación te muestro cómo puedes corregir tu lógica y manejar cookies de manera adecuada en FastAPI.

En FastAPI, la mejor práctica para manejar JWT en cookies es usar los headers Set-Cookie para almacenar el token JWT en una cookie segura, similar a lo que haces en Flask con set_access_cookies(). Aquí te dejo un ejemplo con las correcciones necesarias.
La nueva funcionalidad que mencionas en el segundo fragmento de código no afecta a las cookies. En lugar de establecer una cookie con el token JWT, simplemente devuelve el `access_token` en el cuerpo de la respuesta JSON.

#### Diferencias clave entre los dos enfoques:

1. **Uso de cookies en el primer fragmento:**
   - El primer fragmento de código establece una cookie (`access_token`) en la respuesta utilizando `response.set_cookie()`.
   - La cookie se envía al cliente, y el token se almacena en el navegador del cliente como una cookie. Esto puede ser útil si deseas que el token se maneje automáticamente en futuras solicitudes por el navegador, ya que los navegadores envían cookies con cada solicitud hacia el servidor.
   - La cookie tiene configuraciones adicionales como `httponly`, `secure`, y `samesite` para mejorar la seguridad.

2. **Sin cookies en el segundo fragmento:**
   - El segundo fragmento simplemente retorna el `access_token` dentro del cuerpo de la respuesta JSON sin establecer una cookie.
   - El cliente debe almacenar el token en algún lugar (por ejemplo, en el almacenamiento local o en un estado de la aplicación) y enviarlo manualmente en las cabeceras de autorización de las solicitudes subsiguientes.

#### Impacto de la nueva funcionalidad sobre las cookies:
- **En el primer fragmento**, el token se establece en una cookie, lo que significa que el navegador se encarga automáticamente de enviar el token en cada solicitud al servidor.
- **En el segundo fragmento**, el token no se guarda en una cookie, por lo que el cliente (por ejemplo, una aplicación front-end) debe manejar el almacenamiento y la inclusión manual del token en las cabeceras de la solicitud (generalmente usando el esquema `Bearer` en el encabezado `Authorization`).

**En resumen:**
- La segunda implementación no usa cookies, por lo que no afectará las cookies que se hayan configurado en la primera.
- Si decides usar el segundo fragmento, el cliente deberá manejar el token JWT manualmente, mientras que con el primer fragmento, el servidor maneja el envío del token a través de cookies.

Si deseas una solución que combine la capacidad de manejar el token mediante cookies (como en el primer fragmento) y que también sea accesible a través de solicitudes JSON (como en el segundo fragmento), deberás usar ambos mecanismos, o bien hacer que el servidor decida dinámicamente si establecer una cookie o devolver el token en la respuesta JSON según la solicitud del cliente.
- con  cookies
```python
@auth_router.post("/signin", response_model=Token)
async def signin(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Buscamos el usuario por el nombre de usuario
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not user.check_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generamos el token JWT
    access_token = create_access_token(data={"sub": str(user.id)})

    # Preparamos la respuesta JSON con los detalles del usuario
    response_data = {
        "access_token": access_token,
        "token_type": "bearer",
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "roles": [role.name for role in user.roles]
    }

    # Creamos la respuesta con un objeto JSON
    response = JSONResponse(content=jsonable_encoder(response_data))
    
    # Establecemos la cookie con el token de acceso
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True,  # La cookie solo es accesible desde el servidor (no por JavaScript)
        max_age=timedelta(hours=settings.jwt_expires_hours),  # Duración de la cookie
        expires=timedelta(hours=settings.jwt_expires_hours),  # Duración de la cookie
        secure=True,  # Habilitar solo en HTTPS
        samesite="Strict"  # Estrictamente solo en el mismo sitio
    )
    
    return response
```

- sin  cookies
```python
@auth_router.post("/signin", response_model=Token)
async def signin(request: Request, db: Session = Depends(get_db)):
    # Verifica el tipo de contenido
    content_type = request.headers.get("Content-Type")
    
    # Si el tipo de contenido es JSON
    if "application/json" in content_type:
        # Extrae los datos del cuerpo de la solicitud como JSON
        body = await request.json()
        username = body.get("username")
        password = body.get("password")
    
    # Si el tipo de contenido es form-urlencoded
    elif "application/x-www-form-urlencoded" in content_type:
        # Extrae los datos del formulario
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")
    
    else:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported Media Type. Use either application/json or application/x-www-form-urlencoded."
        )
    
    # Verifica si los campos están presentes
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required."
        )
    
    # Busca al usuario en la base de datos
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.check_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Genera el token JWT
    access_token = create_access_token(data={"sub": str(user.id)})

    # Prepara la respuesta con los detalles del usuario
    response_data = {
        "access_token": access_token,
        "token_type": "bearer",
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "roles": [role.name for role in user.roles]
    }

    # Retorna la respuesta con el token y los detalles del usuario
    return JSONResponse(content=jsonable_encoder(response_data))
```

---