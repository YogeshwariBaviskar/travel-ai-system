import Link from "next/link";

export default function HomePage() {
  return (
    <div className="text-center py-20">
      <h1 className="text-5xl font-bold text-gray-900 mb-4">
        Plan your dream trip
        <span className="text-brand-600"> with AI</span>
      </h1>
      <p className="text-xl text-gray-500 mb-10 max-w-xl mx-auto">
        Eight specialized AI agents collaborate to build your perfect itinerary — flights,
        hotels, activities, and budget all optimized for you.
      </p>
      <div className="flex justify-center gap-4">
        <Link
          href="/login"
          className="bg-brand-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-brand-700 transition-colors text-lg"
        >
          Get Started
        </Link>
        <Link
          href="/trips"
          className="bg-white text-brand-600 border border-brand-200 px-8 py-3 rounded-xl font-semibold hover:bg-brand-50 transition-colors text-lg"
        >
          My Trips
        </Link>
      </div>

      <div className="mt-20 grid grid-cols-3 gap-6 text-left">
        {[
          { icon: "🧠", title: "8 Specialized Agents", desc: "Planner, flight, hotel, experience, budget and more agents collaborate in real time." },
          { icon: "💰", title: "Budget-Aware", desc: "Every itinerary is automatically tailored to fit within your budget." },
          { icon: "🔁", title: "Real-Time Replanning", desc: "Flight delayed? The system adapts your entire trip automatically." },
        ].map((f) => (
          <div key={f.title} className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
            <div className="text-3xl mb-3">{f.icon}</div>
            <h3 className="font-bold text-gray-800 mb-1">{f.title}</h3>
            <p className="text-sm text-gray-500">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
