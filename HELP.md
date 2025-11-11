### ⚙️ Cómo registrar tu OAuth App GitHub

En GitHub → [Settings → Developer settings → OAuth Apps → New OAuth App](https://github.com/settings/developers)

Completa así 👇

| Campo                          | Qué poner                                                                                                                                                        | Ejemplo                                                 |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| **Application name**           | Nombre legible del proyecto (no importa si es local).                                                                                                            | `test_apps_logins` ✅                                    |
| **Homepage URL**               | La URL base donde corre tu app. Debe empezar con `http://` o `https://`. <br>Si usas FastAPI local: `http://localhost:8000` (o el puerto donde esté tu backend). | `http://localhost:8000` ✅                               |
| **Application description**    | (Opcional) breve texto.                                                                                                                                          | `Sistema de autenticación local de pruebas con FastAPI` |
| **Authorization callback URL** | **Crítico:** aquí GitHub redirigirá después del login.<br>Debe coincidir con la ruta de callback en tu backend.                                                  | `http://localhost:8000/auth/github/callback` ✅          |
| **Enable Device Flow**         | Déjalo **desactivado** (solo se usa para apps sin navegador o CLI).                                                                                              | ❌                                                       |

---

## 🔹 Ejemplo completo (para tu caso)

| Campo                          | Valor recomendado                                |
| ------------------------------ | ------------------------------------------------ |
| **Application name**           | `test_apps_logins`                               |
| **Homepage URL**               | `http://localhost:8000`                          |
| **Application description**    | `Autenticación OAuth local con GitHub y FastAPI` |
| **Authorization callback URL** | `http://localhost:8000/auth/github/callback`     |

---
