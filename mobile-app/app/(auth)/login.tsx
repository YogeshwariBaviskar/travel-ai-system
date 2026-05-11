import { useEffect } from "react";
import { View, Text, TouchableOpacity, StyleSheet, Image } from "react-native";
import * as AuthSession from "expo-auth-session";
import * as WebBrowser from "expo-web-browser";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useRouter } from "expo-router";
import { useStore } from "@/lib/store";
import { api, WS_BASE } from "@/lib/api";

WebBrowser.maybeCompleteAuthSession();

const API_BASE = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";
const REDIRECT_URI = AuthSession.makeRedirectUri({ scheme: "travelai" });

export default function LoginScreen() {
  const router = useRouter();
  const setUser = useStore((s) => s.setUser);
  const setToken = useStore((s) => s.setToken);

  async function handleGoogleLogin() {
    const authUrl =
      `${API_BASE}/api/auth/google?` +
      `redirect_uri=${encodeURIComponent(REDIRECT_URI)}`;

    const result = await WebBrowser.openAuthSessionAsync(authUrl, REDIRECT_URI);

    if (result.type === "success" && result.url) {
      const url = new URL(result.url);
      const token = url.searchParams.get("token");
      if (token) {
        await AsyncStorage.setItem("access_token", token);
        setToken(token);
        const user = await api.auth.me();
        setUser(user);
        router.replace("/(tabs)/trips");
      }
    }
  }

  return (
    <View style={styles.container}>
      <View style={styles.hero}>
        <Text style={styles.logo}>✈️</Text>
        <Text style={styles.title}>Travel AI</Text>
        <Text style={styles.subtitle}>Your personal AI travel planner</Text>
      </View>

      <View style={styles.features}>
        {["Multi-agent itinerary planning", "Real-time disruption alerts", "Budget-aware recommendations"].map(
          (f) => (
            <View key={f} style={styles.featureRow}>
              <Text style={styles.featureBullet}>•</Text>
              <Text style={styles.featureText}>{f}</Text>
            </View>
          )
        )}
      </View>

      <TouchableOpacity style={styles.button} onPress={handleGoogleLogin}>
        <Text style={styles.buttonText}>Continue with Google</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff", padding: 32, justifyContent: "space-between" },
  hero: { flex: 1, justifyContent: "center", alignItems: "center" },
  logo: { fontSize: 64, marginBottom: 16 },
  title: { fontSize: 36, fontWeight: "800", color: "#1a1a2e" },
  subtitle: { fontSize: 16, color: "#6b7280", marginTop: 8 },
  features: { marginBottom: 32 },
  featureRow: { flexDirection: "row", gap: 8, marginBottom: 8 },
  featureBullet: { color: "#4f46e5", fontWeight: "700" },
  featureText: { color: "#374151", fontSize: 15 },
  button: { backgroundColor: "#4f46e5", borderRadius: 14, padding: 16, alignItems: "center" },
  buttonText: { color: "#fff", fontWeight: "700", fontSize: 16 },
});
