# Plan de Implementación: Google OAuth 2.0

Integración de autenticación con Google OAuth 2.0 al sistema existente de auth (JWT + email/password).

## Configuración Previa en Google Cloud Console

> [!IMPORTANT]
> Antes de implementar el código, necesitas tener configurado en Google Cloud Console:
> - Proyecto creado con OAuth 2.0 habilitado
> - **Client ID** y **Client Secret** generados
> - **Authorized redirect URIs** configurados (ej: `http://localhost:3000/api/auth/callback/google`)

---

## Cambios Propuestos

### 1. Backend - Configuración

#### [MODIFY] [config.py](file:///c:/Users/gasto/Desktop/Programacion/DATA-OILERS/03-enterprise-ai-platform/enterprise-ai-platform/services/api/app/core/config.py)

Agregar variables de entorno para Google OAuth:

```diff
+    # Google OAuth
+    GOOGLE_CLIENT_ID: str = ""
+    GOOGLE_CLIENT_SECRET: str = ""
+    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/api/auth/callback/google"
```

#### [MODIFY] [.env.docker](file:///c:/Users/gasto/Desktop/Programacion/DATA-OILERS/03-enterprise-ai-platform/enterprise-ai-platform/services/api/.env.docker)

Agregar las credenciales de Google:

```diff
+GOOGLE_CLIENT_ID=tu-client-id-aqui
+GOOGLE_CLIENT_SECRET=tu-client-secret-aqui
```

---

### 2. Backend - Modelo de Usuario

#### [MODIFY] [user.py (ORM)](file:///c:/Users/gasto/Desktop/Programacion/DATA-OILERS/03-enterprise-ai-platform/enterprise-ai-platform/services/api/app/infrastructure/db/orm/user.py)

Modificar el modelo para soportar OAuth providers:

```diff
 class UserORM(Base):
     __tablename__ = "users"
     ...
-    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
+    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
+    
+    # OAuth fields
+    oauth_provider: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
+    oauth_provider_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
+    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
```

> [!WARNING]
> `password_hash` cambia a nullable para permitir usuarios que solo usan OAuth (sin contraseña local).

#### [NEW] Migración Alembic

Crear nueva migración en `services/api/alembic/versions/`:

```bash
cd services/api
alembic revision --autogenerate -m "add_oauth_fields_to_users"
```

---

### 3. Backend - Repositorio de Usuario

#### [MODIFY] [user_repo.py](file:///c:/Users/gasto/Desktop/Programacion/DATA-OILERS/03-enterprise-ai-platform/enterprise-ai-platform/services/api/app/infrastructure/db/repositories/user_repo.py)

Agregar método para buscar/crear usuario por OAuth:

```python
async def get_by_oauth(self, provider: str, provider_id: str) -> UserORM | None:
    stmt = (
        select(UserORM)
        .options(selectinload(UserORM.role))
        .where(UserORM.oauth_provider == provider)
        .where(UserORM.oauth_provider_id == provider_id)
    )
    result = await self.db.execute(stmt)
    return result.scalar_one_or_none()

async def create_oauth_user(
    self,
    *,
    email: str,
    oauth_provider: str,
    oauth_provider_id: str,
    tenant_id: UUID,
    role_id: UUID,
    avatar_url: str | None = None,
) -> UserORM:
    user = UserORM(
        email=email,
        password_hash=None,  # Sin password para OAuth
        oauth_provider=oauth_provider,
        oauth_provider_id=oauth_provider_id,
        avatar_url=avatar_url,
        tenant_id=tenant_id,
        role_id=role_id,
        is_active=True,
    )
    self.db.add(user)
    await self.db.commit()
    await self.db.refresh(user)
    return await self.get_by_id(user.id)
```

---

### 4. Backend - Servicio OAuth

#### [NEW] [google_oauth_service.py](file:///c:/Users/gasto/Desktop/Programacion/DATA-OILERS/03-enterprise-ai-platform/enterprise-ai-platform/services/api/app/application/services/google_oauth_service.py)

```python
import httpx
from app.core.config import settings

class GoogleOAuthService:
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    async def exchange_code_for_tokens(self, code: str) -> dict:
        """Intercambia el código de autorización por tokens."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> dict:
        """Obtiene información del usuario de Google."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()
```

---

### 5. Backend - Endpoint de Callback

#### [MODIFY] [auth.py (routes)](file:///c:/Users/gasto/Desktop/Programacion/DATA-OILERS/03-enterprise-ai-platform/enterprise-ai-platform/services/api/app/presentation/http/routes/auth.py)

Agregar endpoint para callback de Google:

```python
from app.application.services.google_oauth_service import GoogleOAuthService

@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Callback de Google OAuth - intercambia código por token y crea/obtiene usuario."""
    google_service = GoogleOAuthService()
    
    # 1. Intercambiar código por tokens
    tokens = await google_service.exchange_code_for_tokens(code)
    access_token = tokens["access_token"]
    
    # 2. Obtener info del usuario
    user_info = await google_service.get_user_info(access_token)
    google_id = user_info["id"]
    email = user_info["email"]
    avatar = user_info.get("picture")
    
    # 3. Buscar o crear usuario
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    
    user = await user_repo.get_by_oauth("google", google_id)
    
    if not user:
        # Verificar si existe por email (vincular cuentas)
        user = await user_repo.get_by_email(email)
        if user:
            # Actualizar usuario existente con OAuth
            user.oauth_provider = "google"
            user.oauth_provider_id = google_id
            user.avatar_url = avatar
            await db.commit()
        else:
            # Crear nuevo usuario OAuth
            role = await role_repo.get_by_name(RoleName.PRIVATE.value)
            tenant_id = UUID("00000000-0000-0000-0000-000000000000")
            user = await user_repo.create_oauth_user(
                email=email,
                oauth_provider="google",
                oauth_provider_id=google_id,
                avatar_url=avatar,
                tenant_id=tenant_id,
                role_id=role.id,
            )
    
    # 4. Generar JWT
    token = create_access_token(
        subject=str(user.id),
        role=user.role.name,
        tenant_id=str(user.tenant_id),
    )
    
    return TokenResponse(access_token=token, user=_to_user_response(user))

@router.get("/google/url")
async def google_auth_url():
    """Retorna la URL de autorización de Google."""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return {"url": f"https://accounts.google.com/o/oauth2/v2/auth?{query}"}
```

---

### 6. Frontend - NextAuth (Opción Recomendada)

#### [NEW] Instalar dependencias

```bash
cd frontends/rag-chat
npm install next-auth
```

#### [NEW] [route.ts](file:///c:/Users/gasto/Desktop/Programacion/DATA-OILERS/03-enterprise-ai-platform/enterprise-ai-platform/frontends/rag-chat/app/api/auth/[...nextauth]/route.ts)

Configurar NextAuth con Google provider:

```typescript
import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";

const handler = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider === "google") {
        // Llamar al backend para sincronizar usuario
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/google/callback?code=${account.access_token}`,
          { method: "GET" }
        );
        // Manejar respuesta...
      }
      return true;
    },
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
      }
      return token;
    },
  },
});

export { handler as GET, handler as POST };
```

#### [NEW] [.env.local](file:///c:/Users/gasto/Desktop/Programacion/DATA-OILERS/03-enterprise-ai-platform/enterprise-ai-platform/frontends/rag-chat/.env.local)

```env
GOOGLE_CLIENT_ID=tu-client-id
GOOGLE_CLIENT_SECRET=tu-client-secret
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=tu-secret-aleatorio
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

### 7. Frontend - Componente de Login

#### [NEW] [GoogleSignInButton.tsx](file:///c:/Users/gasto/Desktop/Programacion/DATA-OILERS/03-enterprise-ai-platform/enterprise-ai-platform/frontends/rag-chat/components/auth/GoogleSignInButton.tsx)

```tsx
"use client";

import { signIn } from "next-auth/react";

export function GoogleSignInButton() {
  return (
    <button
      onClick={() => signIn("google")}
      className="flex items-center gap-3 px-6 py-3 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
    >
      <svg className="w-5 h-5" viewBox="0 0 24 24">
        {/* Google icon SVG */}
      </svg>
      <span className="text-gray-700 font-medium">Continuar con Google</span>
    </button>
  );
}
```

---

## Resumen de Archivos

| Componente | Archivo | Acción |
|------------|---------|--------|
| Backend Config | [app/core/config.py](file:///c:/Users/gasto/Desktop/Programacion/DATA-OILERS/03-enterprise-ai-platform/enterprise-ai-platform/services/api/app/core/config.py) | MODIFY |
| Backend Env | [.env.docker](file:///c:/Users/gasto/Desktop/Programacion/DATA-OILERS/03-enterprise-ai-platform/enterprise-ai-platform/services/api/.env.docker) | MODIFY |
| Backend ORM | [app/infrastructure/db/orm/user.py](file:///c:/Users/gasto/Desktop/Programacion/DATA-OILERS/03-enterprise-ai-platform/enterprise-ai-platform/services/api/app/infrastructure/db/orm/user.py) | MODIFY |
| Backend Repo | [app/infrastructure/db/repositories/user_repo.py](file:///c:/Users/gasto/Desktop/Programacion/DATA-OILERS/03-enterprise-ai-platform/enterprise-ai-platform/services/api/app/infrastructure/db/repositories/user_repo.py) | MODIFY |
| Backend Service | `app/application/services/google_oauth_service.py` | NEW |
| Backend Routes | [app/presentation/http/routes/auth.py](file:///c:/Users/gasto/Desktop/Programacion/DATA-OILERS/03-enterprise-ai-platform/enterprise-ai-platform/services/api/app/presentation/http/routes/auth.py) | MODIFY |
| Backend Migration | `alembic/versions/xxx_add_oauth_fields.py` | NEW |
| Frontend Auth | `app/api/auth/[...nextauth]/route.ts` | NEW |
| Frontend Env | `.env.local` | NEW |
| Frontend UI | `components/auth/GoogleSignInButton.tsx` | NEW |

---

## Plan de Verificación

### Tests Manuales

> [!NOTE]
> No se encontraron tests automatizados existentes en el proyecto. La verificación se realizará manualmente.

1. **Verificar migración de DB**:
   ```bash
   cd services/api
   alembic upgrade head
   # Verificar que la tabla users tenga las columnas oauth_provider, oauth_provider_id, avatar_url
   ```

2. **Probar endpoint de URL de auth**:
   ```bash
   curl http://localhost:8000/api/v1/auth/google/url
   # Debe retornar JSON con la URL de Google OAuth
   ```

3. **Flujo completo de login**:
   - Abrir `http://localhost:3000` en el navegador
   - Hacer clic en "Continuar con Google"
   - Autenticarse con cuenta de Google
   - Verificar redirección exitosa y token JWT generado

4. **Verificar usuario en DB**:
   ```sql
   SELECT id, email, oauth_provider, oauth_provider_id 
   FROM users 
   WHERE oauth_provider = 'google';
   ```

### Verificaciones de Usuario

Por favor confirma:
1. ¿El frontend debe usar NextAuth o prefieres una implementación manual con fetch?
2. ¿Los usuarios OAuth deben poder configurar una contraseña local después?
3. ¿Se debe permitir vincular cuenta Google a usuarios existentes con email/password?
