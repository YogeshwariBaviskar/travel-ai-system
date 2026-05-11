import { useEffect, useState } from "react";
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, ActivityIndicator } from "react-native";
import { useRouter } from "expo-router";
import { api } from "@/lib/api";
import { useStore } from "@/lib/store";

const STATUS_COLORS: Record<string, string> = {
  complete: "#10b981",
  planning: "#f59e0b",
  replanning: "#f59e0b",
  failed: "#ef4444",
};

export default function TripsScreen() {
  const router = useRouter();
  const { trips, setTrips } = useStore();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  async function loadTrips() {
    try {
      const data = await api.trips.list();
      setTrips(data);
    } catch {
      router.replace("/(auth)/login");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => { loadTrips(); }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#4f46e5" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.header}>My Trips</Text>
      <FlatList
        data={trips}
        keyExtractor={(t) => t.id}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadTrips(); }} />}
        contentContainerStyle={trips.length === 0 ? styles.emptyContainer : { paddingBottom: 24 }}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyIcon}>✈️</Text>
            <Text style={styles.emptyText}>No trips yet</Text>
            <Text style={styles.emptySubtext}>Tap "New Trip" to start planning</Text>
          </View>
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.card}
            onPress={() => router.push(`/trip/${item.id}`)}
          >
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>{item.title}</Text>
              <View style={[styles.badge, { backgroundColor: STATUS_COLORS[item.status] + "20" }]}>
                <Text style={[styles.badgeText, { color: STATUS_COLORS[item.status] }]}>
                  {item.status}
                </Text>
              </View>
            </View>
            {item.raw_request && (
              <Text style={styles.cardMeta}>
                {item.raw_request.destination as string} · {item.raw_request.start_date as string} → {item.raw_request.end_date as string}
              </Text>
            )}
            {item.raw_request?.budget && (
              <Text style={styles.cardBudget}>Budget: ${(item.raw_request.budget as number).toLocaleString()}</Text>
            )}
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f9fafb", paddingHorizontal: 16, paddingTop: 60 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  header: { fontSize: 28, fontWeight: "800", color: "#111827", marginBottom: 20 },
  card: { backgroundColor: "#fff", borderRadius: 16, padding: 16, marginBottom: 12, shadowColor: "#000", shadowOpacity: 0.05, shadowRadius: 8, elevation: 2 },
  cardHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 4 },
  cardTitle: { fontSize: 16, fontWeight: "700", color: "#111827", flex: 1 },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 20 },
  badgeText: { fontSize: 12, fontWeight: "600" },
  cardMeta: { fontSize: 13, color: "#6b7280", marginBottom: 2 },
  cardBudget: { fontSize: 12, color: "#9ca3af" },
  emptyContainer: { flex: 1, justifyContent: "center" },
  empty: { alignItems: "center", paddingTop: 80 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyText: { fontSize: 20, fontWeight: "700", color: "#374151" },
  emptySubtext: { fontSize: 14, color: "#9ca3af", marginTop: 4 },
});
