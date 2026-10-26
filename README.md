# Auth0-itm-guia3
Taller Guía 3 - Aplicaciones y servicios web (Auth0)
Yulieth Muñoz y Cristobal Mejia

Este es el repositorio de código donde se trabajó el versionamiento del aplicativo realizado para el Taller 3. Se usó Python y se manejó toda la implementación, permisos y personalización desde la interfaz de administración del tenant en la página de Auth0, ambos en el equipo team-0f7sg34

## Diagrama de flujo

```mermaid
flowchart TD
    A([Usuario abre localhost:5000]) --> B{¿Hay sesión activa?}
    B -- Sí --> I[Home muestra el perfil del usuario]
    B -- No --> C[App muestra enlaces Signup y Login]
    C --> D{Inicia sesión o se registra?}
    D -- Login --> E["App redirige a Auth0 (/login)"]
    E --> F[Auth0 muestra Universal Login ITM]
    F --> G[Usuario ingresa correo y contraseña]
    G --> H{¿Credenciales válidas?}
    H -- No --> J[Auth0 muestra error]
    J --> F
    H -- Sí --> K["Auth0 redirige a /callback con código"]
    D -- Signup --> L["App redirige a Auth0 (/signup)"]
    L --> M[Auth0 muestra el formulario de registro]
    M --> N[Usuario ingresa datos de registro]
    N --> K
    K --> O[App canjea el código por tokens]
    O --> P{¿Canje exitoso?}
    P -- No --> Q[Muestra error 400]
    P -- Sí --> R[App guarda la sesión en cookie]
    R --> I
    I --> S{Desea cerrar sesión?}
    S -- Si --> T[Logout/Detener]
    S -- No --> U{Desea modificar sus datos?}
    U -- No --> I
    V -- Si --> W[App muestra formulario de edición de datos]
    W --> X[Usuario añade datos nuevos o edita los existentes]
    X --> Y[App guarda los datos modificados]
    Y --> I
```