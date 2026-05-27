/** Country / city options for company people search (must match agents locations.py). */

export const COUNTRIES = [
  "",
  "India",
  "United States",
  "United Kingdom",
  "Canada",
  "Singapore",
  "United Arab Emirates",
  "Australia",
  "Germany",
] as const;

export const CITIES_BY_COUNTRY: Record<string, string[]> = {
  India: [
    "Delhi",
    "Mumbai",
    "Bengaluru",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Kolkata",
    "Gurgaon",
    "Noida",
    "Ahmedabad",
    "Jaipur",
    "Chandigarh",
  ],
  "United States": [
    "New York",
    "San Francisco",
    "Seattle",
    "Austin",
    "Boston",
    "Chicago",
    "Los Angeles",
  ],
  "United Kingdom": ["London", "Manchester", "Edinburgh", "Birmingham"],
  Canada: ["Toronto", "Vancouver", "Montreal", "Calgary"],
  Singapore: ["Singapore"],
  "United Arab Emirates": ["Dubai", "Abu Dhabi"],
  Australia: ["Sydney", "Melbourne", "Brisbane"],
  Germany: ["Berlin", "Munich", "Frankfurt"],
};
