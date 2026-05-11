import { View, Text, TouchableOpacity, StyleSheet, Alert } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useRouter } from "expo-router";
import { useStore } from "@/lib/store";

export default function ProfileScreen() {
  const router = useRouter();
  const { user, setUser, setToken } = useStore();

  async function logout() {
    await AsyncStorage.removeItem("access_token");
    setUser(null);
    setToken(null);
    router.replace("/(auth)/login");
  }

  if (!user) {
    return (
      <View style={styles.center}>
        <TouchableOpacity style={styles.button} onPress={() => router.replace("/(auth)/login")}>
          <Text style={styles.buttonText}>Log In</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.avatar}>
        <Text style={styles.avatarText}>{user.name?.charAt(0) || user.email.charAt(0)}</Text>
      </View>
      <Text style={styles.name}>{user.name}</Text>
      <Text style={styles.email}>{user.email}</Text>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Account</Text>
        <Text style={styles.cardItem}>Email: {user.email}</Text>
        <Text style={styles.cardItem}>ID: {user.id}</Text>
      </View>

      <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
        <Text style={styles.logoutText}>Log Out</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f9fafb", padding: 24, paddingTop: 60, alignItems: "center" },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  avatar: { width: 80, height: 80, borderRadius: 40, backgroundColor: "#4f46e5", justifyContent: "center", alignItems: "center", marginBottom: 12 },
  avatarText: { color: "#fff", fontSize: 32, fontWeight: "700" },
  name: { fontSize: 22, fontWeight: "700", color: "#111827" },
  email: { fontSize: 14, color: "#6b7280", marginBottom: 24 },
  card: { backgroundColor: "#fff", borderRadius: 16, padding: 16, width: "100%", marginBottom: 16 },
  cardTitle: { fontWeight: "700", color: "#374151", marginBottom: 8 },
  cardItem: { color: "#6b7280", fontSize: 14, marginBottom: 4 },
  button: { backgroundColor: "#4f46e5", borderRadius: 14, padding: 16, paddingHorizontal: 32 },
  buttonText: { color: "#fff", fontWeight: "700", fontSize: 16 },
  logoutBtn: { borderWidth: 1, borderColor: "#ef4444", borderRadius: 14, padding: 14, paddingHorizontal: 32 },
  logoutText: { color: "#ef4444", fontWeight: "700", fontSize: 16 },
});
