const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export default function LoginButton() {
  return <a href={`${API_URL}/auth/login`}>Login with Spotify</a>;
}
