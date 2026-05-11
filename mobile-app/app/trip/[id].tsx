import { useEffect, useRef, useState } from "react";
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert,
} from "react-native";
import MapView, { Marker, PROVIDER_GOOGLE } from "react-native-maps";
import { useLocalSearchParams, useRouter } from "expo-router";
import { api, WS_BASE } from "@/lib/api";
import { useStore } from "@/lib/store";

export default function TripDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const removeTrip = useStore((s) => s.removeTrip);
  const [trip, setTrip] = useState<any>(null);
  const [liveUpdate, setLiveUpdate] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"overview" | "map" | "budget">("overview");
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    api.trips.get(id!).then((t) => { setTrip(t); connectWs(id!); }).finally(() => setLoading(false));
    return () => wsRef.current?.close();
  }, [id]);

  function connectWs(tripId: string) {
    const AsyncStorage = require("@react-native-async-storage/async-storage").default;
    AsyncStorage.getItem("access_token").then((token: string | null) => {
      const ws = new WebSocket(`${WS_BASE}/trips/${tripId}?token=${token || ""}`);
      wsRef.current = ws;
      ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.event === "replan") {
          setLiveUpdate(data);
          Alert.alert("⚠️ Plan Updated", data.replan?.summary || "Your itinerary has been adjusted.");
        }
      };
    });
  }

  async function handleDelete() {
    Alert.alert("Delete Trip", "Are you sure?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete", style: "destructive",
        onPress: async () => {
          await api.trips.delete(id!);
          removeTrip(id!);
          router.back();
        },
      },
    ]);
  }

  if (loading) return <View style={styles.center}><ActivityIndicator size="large" color="#4f46e5" /></View>;
  if (!trip) return <View style={styles.center}><Text>Trip not found</Text></View>;

  const plan = liveUpdate?.plan || trip.plan;
  const isMultiAgent = !!(plan?.flights || plan?.itinerary);
  const days = isMultiAgent ? (plan?.itinerary?.days || []) : (plan?.days || []);
  const budget = plan?.budget_summary;

  // Extract map markers from days
  const markers = days.flatMap((day: any, di: number) =>
    ["morning", "afternoon", "evening"].map((slot) => ({
      key: `${di}-${slot}`,
      title: day[slot]?.name,
      description: day[slot]?.description,
    })).filter((m) => m.title)
  );

  return (
    <View style={styles.container}>
      <View style={styles.topBar}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={styles.back}>← Back</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={handleDelete}>
          <Text style={styles.delete}>Delete</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.title}>{trip.title}</Text>

      {liveUpdate && (
        <View style={styles.alertBanner}>
          <Text style={styles.alertText}>⚠️ {liveUpdate.replan?.summary}</Text>
        </View>
      )}

      <View style={styles.tabs}>
        {(["overview", "map", "budget"] as const).map((t) => (
          <TouchableOpacity
            key={t}
            style={[styles.tab, tab === t && styles.tabActive]}
            onPress={() => setTab(t)}
          >
            <Text style={[styles.tabText, tab === t && styles.tabTextActive]}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {tab === "overview" && (
        <ScrollView style={styles.scroll}>
          {days.map((day: any, i: number) => (
            <View key={i} style={styles.dayCard}>
              <Text style={styles.dayTitle}>Day {i + 1} {day.theme ? `— ${day.theme}` : ""}</Text>
              <Text style={styles.dayDate}>{day.date}</Text>
              {["morning", "afternoon", "evening"].map((slot) =>
                day[slot] ? (
                  <View key={slot} style={styles.slot}>
                    <Text style={styles.slotLabel}>{slot.charAt(0).toUpperCase() + slot.slice(1)}</Text>
                    <Text style={styles.slotName}>{day[slot].name}</Text>
                    <Text style={styles.slotDesc}>{day[slot].description}</Text>
                    <Text style={styles.slotMeta}>${day[slot].estimated_cost} · {day[slot].duration_hours}h</Text>
                  </View>
                ) : null
              )}
            </View>
          ))}
        </ScrollView>
      )}

      {tab === "map" && (
        <MapView
          provider={PROVIDER_GOOGLE}
          style={styles.map}
          initialRegion={{ latitude: 35.6762, longitude: 139.6503, latitudeDelta: 0.1, longitudeDelta: 0.1 }}
        >
          {markers.map((m: any) => (
            <Marker key={m.key} coordinate={{ latitude: 35.6762, longitude: 139.6503 }} title={m.title} description={m.description} />
          ))}
        </MapView>
      )}

      {tab === "budget" && budget && (
        <ScrollView style={styles.scroll}>
          <View style={styles.budgetCard}>
            <Text style={styles.budgetStatus}>
              {budget.is_within_budget ? "✓ Within Budget" : "⚠️ Over Budget"}
            </Text>
            <Text style={styles.budgetLine}>Total Budget: ${budget.total_budget?.toLocaleString()}</Text>
            <Text style={styles.budgetLine}>Estimated Cost: ${budget.total_estimated_cost?.toLocaleString()}</Text>
            {budget.savings_tips?.map((tip: string, i: number) => (
              <Text key={i} style={styles.tip}>• {tip}</Text>
            ))}
          </View>
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f9fafb" },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  topBar: { flexDirection: "row", justifyContent: "space-between", padding: 16, paddingTop: 56 },
  back: { color: "#4f46e5", fontWeight: "600", fontSize: 15 },
  delete: { color: "#ef4444", fontWeight: "600", fontSize: 15 },
  title: { fontSize: 22, fontWeight: "800", color: "#111827", paddingHorizontal: 16, marginBottom: 8 },
  alertBanner: { backgroundColor: "#fef3c7", borderLeftWidth: 4, borderLeftColor: "#f59e0b", margin: 16, padding: 12, borderRadius: 8 },
  alertText: { color: "#92400e", fontSize: 13 },
  tabs: { flexDirection: "row", paddingHorizontal: 16, gap: 8, marginBottom: 8 },
  tab: { paddingHorizontal: 16, paddingVertical: 6, borderRadius: 20, backgroundColor: "#e5e7eb" },
  tabActive: { backgroundColor: "#4f46e5" },
  tabText: { color: "#6b7280", fontWeight: "600", fontSize: 13 },
  tabTextActive: { color: "#fff" },
  scroll: { flex: 1 },
  dayCard: { backgroundColor: "#fff", margin: 8, borderRadius: 16, padding: 16 },
  dayTitle: { fontSize: 16, fontWeight: "700", color: "#111827" },
  dayDate: { color: "#9ca3af", fontSize: 12, marginBottom: 8 },
  slot: { paddingVertical: 8, borderTopWidth: 1, borderTopColor: "#f3f4f6" },
  slotLabel: { fontSize: 11, color: "#9ca3af", textTransform: "uppercase", fontWeight: "600" },
  slotName: { fontWeight: "700", color: "#374151" },
  slotDesc: { color: "#6b7280", fontSize: 13 },
  slotMeta: { color: "#9ca3af", fontSize: 12, marginTop: 2 },
  map: { flex: 1, margin: 8, borderRadius: 16, overflow: "hidden" },
  budgetCard: { backgroundColor: "#fff", margin: 8, borderRadius: 16, padding: 16 },
  budgetStatus: { fontSize: 18, fontWeight: "700", color: "#111827", marginBottom: 12 },
  budgetLine: { color: "#374151", fontSize: 15, marginBottom: 6 },
  tip: { color: "#6b7280", fontSize: 13, marginTop: 4 },
});
