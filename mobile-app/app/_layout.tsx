import { useEffect } from "react";
import { Stack } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useStore } from "@/lib/store";
import { api } from "@/lib/api";
import { registerForPushNotifications, addResponseListener } from "@/lib/notifications";

export default function RootLayout() {
  const setUser = useStore((s) => s.setUser);
  const setToken = useStore((s) => s.setToken);

  useEffect(() => {
    async function init() {
      const token = await AsyncStorage.getItem("access_token");
      if (token) {
        setToken(token);
        try {
          const user = await api.auth.me();
          setUser(user);
        } catch {
          await AsyncStorage.removeItem("access_token");
          setToken(null);
        }
      }

      const pushToken = await registerForPushNotifications();
      if (pushToken) console.log("Push token:", pushToken);

      addResponseListener((response) => {
        const tripId = response.notification.request.content.data?.trip_id;
        // Navigation handled by expo-router deep links
        if (tripId) console.log("Notification tap for trip:", tripId);
      });
    }
    init();
  }, []);

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="(auth)" />
      <Stack.Screen name="(tabs)" />
    </Stack>
  );
}
