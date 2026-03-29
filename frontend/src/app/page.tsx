import { redirect } from "next/navigation";

export default function RootPage() {
    // Redirigir automáticamente al login al entrar a la raíz /
    redirect("/login");
}
