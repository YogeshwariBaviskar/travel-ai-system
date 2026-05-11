import { useState } from "react";
import {
  View, Text, TextInput, TouchableOpacity, ScrollView,
  StyleSheet, ActivityIndicator, Alert, Switch,
} from "react-native";
import { useRouter } from "expo-router";
import { api } from "@/lib/api";
import { useStore } from "@/lib/store";

const INTERESTS = ["Culture", "Food", "Adventure", "Nature", "Shopping", "Nightlife", "History", "Art", "Beach", "Hiking"];

export default function NewTripScreen() {
  const router = useRouter();
  const addTrip = useStore((s) => s.addTrip);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    destination: "",
    start_date: "",
    end_date: "",
    budget: "2000",
    num_travelers: "1",
    origin_airport: "JFK",
    interests: [] as string[],
    use_multi_agent: true,
  });

  function toggle(interest: string) {
    setForm((p) => ({
      ...p,
      interests: p.interests.includes(interest)
        ? p.interests.filter((i) => i !== interest)
        : [...p.interests, interest],
    }));
  }

  async function submit() {
    if (!form.destination || !form.start_date || !form.end_date) {
      Alert.alert("Missing fields", "Please fill in destination and dates.");
      return;
    }
    setLoading(true);
    try {
      const trip = await api.trips.create({
        ...form,
        budget: Number(form.budget),
        num_travelers: Number(form.num_travelers),
      });
      addTrip(trip);
      router.push(`/trip/${trip.id}`);
    } catch (e: any) {
      Alert.alert("Error", e.message || "Failed to create trip");
    } finally {
      setLoading(false);
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }}>
      <Text style={styles.header}>Plan a New Trip</Text>

      <Text style={styles.label}>Destination</Text>
      <TextInput
        style={styles.input}
        placeholder="e.g. Tokyo, Japan"
        value={form.destination}
        onChangeText={(v) => setForm((p) => ({ ...p, destination: v }))}
      />

      <View style={styles.row}>
        <View style={styles.half}>
          <Text style={styles.label}>Start Date</Text>
          <TextInput style={styles.input} placeholder="YYYY-MM-DD" value={form.start_date}
            onChangeText={(v) => setForm((p) => ({ ...p, start_date: v }))} />
        </View>
        <View style={styles.half}>
          <Text style={styles.label}>End Date</Text>
          <TextInput style={styles.input} placeholder="YYYY-MM-DD" value={form.end_date}
            onChangeText={(v) => setForm((p) => ({ ...p, end_date: v }))} />
        </View>
      </View>

      <View style={styles.row}>
        <View style={styles.half}>
          <Text style={styles.label}>Budget (USD)</Text>
          <TextInput style={styles.input} keyboardType="numeric" value={form.budget}
            onChangeText={(v) => setForm((p) => ({ ...p, budget: v }))} />
        </View>
        <View style={styles.half}>
          <Text style={styles.label}>Travelers</Text>
          <TextInput style={styles.input} keyboardType="numeric" value={form.num_travelers}
            onChangeText={(v) => setForm((p) => ({ ...p, num_travelers: v }))} />
        </View>
      </View>

      <Text style={styles.label}>Origin Airport</Text>
      <TextInput style={styles.input} placeholder="e.g. JFK" autoCapitalize="characters"
        value={form.origin_airport} onChangeText={(v) => setForm((p) => ({ ...p, origin_airport: v.toUpperCase() }))} />

      <Text style={styles.label}>Interests</Text>
      <View style={styles.chips}>
        {INTERESTS.map((i) => (
          <TouchableOpacity
            key={i}
            onPress={() => toggle(i)}
            style={[styles.chip, form.interests.includes(i) && styles.chipActive]}
          >
            <Text style={[styles.chipText, form.interests.includes(i) && styles.chipTextActive]}>{i}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.switchRow}>
        <Text style={styles.label}>Multi-Agent Planning</Text>
        <Switch
          value={form.use_multi_agent}
          onValueChange={(v) => setForm((p) => ({ ...p, use_multi_agent: v }))}
          trackColor={{ true: "#4f46e5" }}
        />
      </View>

      <TouchableOpacity style={[styles.button, loading && styles.buttonDisabled]} onPress={submit} disabled={loading}>
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Generate Itinerary</Text>}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f9fafb", padding: 16, paddingTop: 60 },
  header: { fontSize: 28, fontWeight: "800", color: "#111827", marginBottom: 24 },
  label: { fontSize: 13, fontWeight: "600", color: "#374151", marginBottom: 6, marginTop: 12 },
  input: { backgroundColor: "#fff", borderRadius: 10, borderWidth: 1, borderColor: "#e5e7eb", padding: 12, fontSize: 15 },
  row: { flexDirection: "row", gap: 12 },
  half: { flex: 1 },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, borderWidth: 1, borderColor: "#d1d5db", backgroundColor: "#fff" },
  chipActive: { backgroundColor: "#4f46e5", borderColor: "#4f46e5" },
  chipText: { color: "#6b7280", fontSize: 13 },
  chipTextActive: { color: "#fff" },
  switchRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginTop: 12 },
  button: { backgroundColor: "#4f46e5", borderRadius: 14, padding: 16, alignItems: "center", marginTop: 24 },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: "#fff", fontWeight: "700", fontSize: 16 },
});
