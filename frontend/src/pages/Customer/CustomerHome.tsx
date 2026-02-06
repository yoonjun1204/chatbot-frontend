// frontend/src/pages/Customer/CustomerHome.tsx
import React from "react";
import ChatWidget from "../../components/Customer/ChatWidget";
import { useAuth } from "../../auth/AuthContext";
import {
  Shirt,
  LogOut,
  ShoppingBag,
  ChevronRight,
  Star,
  Truck,
  ShieldCheck,
  MessageSquare,
  User
} from "lucide-react";

const CustomerHome: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-white text-slate-900 font-sans selection:bg-blue-100 selection:text-blue-900">

      {/* --- NAVIGATION --- */}
      <header className="sticky top-0 z-40 w-full bg-white/80 backdrop-blur-md border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2">
              <div className="bg-blue-600 p-1.5 rounded-lg text-white">
                <Shirt size={20} />
              </div>
              <span className="text-xl font-bold tracking-tight">Shirtify</span>
            </div>
            <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
              <a href="#products" className="hover:text-blue-600 transition-colors">Products</a>
              <a href="#about" className="hover:text-blue-600 transition-colors">About</a>
              <a href="#support" className="hover:text-blue-600 transition-colors">Support</a>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            {user ? (
              <div className="flex items-center gap-3 bg-slate-50 pl-3 pr-1 py-1 rounded-full border border-slate-200">
                <div className="flex items-center gap-2">
                  <User size={14} className="text-slate-400" />
                  <span className="text-xs font-semibold text-slate-600">{user.email}</span>
                </div>
                <button
                  onClick={logout}
                  className="bg-white p-1.5 rounded-full text-slate-400 hover:text-red-500 hover:shadow-sm transition-all border border-slate-200"
                  title="Logout"
                >
                  <LogOut size={16} />
                </button>
              </div>
            ) : (
              <a href="/login" className="text-sm font-bold text-blue-600 hover:text-blue-700">Sign In</a>
            )}
          </div>
        </div>
      </header>

      {/* --- HERO SECTION --- */}
      <section className="relative pt-16 pb-24 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="relative z-10 text-center lg:text-left">
            <span className="inline-block px-4 py-1.5 mb-6 text-xs font-bold tracking-widest text-blue-600 uppercase bg-blue-50 rounded-full">
              New Collection 2026
            </span>
            <h1 className="text-5xl lg:text-6xl font-extrabold text-slate-900 leading-[1.1] mb-6">
              Crisp, Comfortable <br />
              <span className="text-blue-600">Shirts for Every Day</span>
            </h1>
            <p className="text-lg text-slate-500 mb-10 max-w-lg mx-auto lg:mx-0 leading-relaxed">
              Discover premium cotton blends designed for modern life. From boardroom meetings to weekend coffee, we ensure you always look sharp.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4">
              <a href="#products" className="group bg-slate-900 text-white px-8 py-4 rounded-full font-bold flex items-center gap-2 hover:bg-slate-800 transition-all shadow-xl shadow-slate-200">
                Browse Collection
                <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </a>
              <div className="flex items-center gap-2 text-sm text-slate-400 font-medium px-4">
                <Star size={16} className="text-yellow-400 fill-yellow-400" />
                4.9/5 Average Rating
              </div>
            </div>
          </div>

          <div className="relative">
            {/* Visual Placeholder for Hero Image */}
            <div className="aspect-[4/5] bg-slate-100 rounded-[2rem] overflow-hidden relative shadow-2xl rotate-2 hover:rotate-0 transition-transform duration-500">
              <div className="absolute inset-0 bg-gradient-to-tr from-slate-200 to-transparent opacity-50" />
              <div className="absolute bottom-8 left-8 right-8 bg-white/90 backdrop-blur p-6 rounded-2xl border border-white/20 shadow-lg">
                <p className="text-xs font-bold text-blue-600 uppercase mb-1">New Arrival</p>
                <h3 className="text-xl font-bold text-slate-900">Oxford Slim Fit Shirt</h3>
                <div className="flex items-center justify-between mt-4">
                  <span className="text-2xl font-black text-slate-900">$49.90</span>
                  <button className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 transition-colors">
                    <ShoppingBag size={20} />
                  </button>
                </div>
              </div>
            </div>
            {/* Decorative element */}
            <div className="absolute -top-6 -right-6 w-32 h-32 bg-blue-50 rounded-full -z-10 blur-2xl" />
          </div>
        </div>
      </section>

      {/* --- PRODUCT GRID --- */}
      <section id="products" className="py-24 bg-slate-50/50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">Featured Essentials</h2>
            <p className="text-slate-500 max-w-2xl mx-auto">
              A curated selection of our most loved pieces. Can't find your size? Ask our AI assistant for a personalized recommendation.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { name: "Classic White Oxford", price: "$45.00", desc: "Pure cotton, non-iron finish." },
              { name: "Casual Denim Shirt", price: "$59.00", desc: "Soft-washed indigo dye." },
              { name: "Midnight Slim Fit", price: "$52.00", desc: "Minimalist, modern tailoring." }
            ].map((product, i) => (
              <div key={i} className="group bg-white rounded-3xl p-4 border border-slate-100 hover:shadow-xl hover:shadow-slate-200/50 transition-all duration-300 cursor-pointer">
                <div className="aspect-square bg-slate-100 rounded-2xl mb-6 overflow-hidden relative">
                  <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
                <div className="px-2">
                  <h3 className="text-lg font-bold text-slate-900 mb-1 group-hover:text-blue-600 transition-colors">{product.name}</h3>
                  <p className="text-sm text-slate-500 mb-4">{product.desc}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-xl font-bold text-slate-900">{product.price}</span>
                    <button className="text-blue-600 font-bold text-sm flex items-center gap-1 hover:underline">
                      View Details
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* --- INFO / ABOUT SECTION --- */}
      <section id="about" className="py-24 border-t border-slate-100">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {[
              {
                title: "Premium Materials",
                desc: "Every thread is chosen for high breathability and extreme durability.",
                icon: ShieldCheck,
                color: "text-emerald-500",
                bg: "bg-emerald-50"
              },
              {
                title: "Fast Exchanges",
                desc: "30-day hassle-free returns. We want you to find the perfect fit every time.",
                icon: Truck,
                color: "text-blue-500",
                bg: "bg-blue-50"
              },
              {
                title: "Smart Assistance",
                desc: "Our AI-powered chat is ready 24/7 to help with orders and styling advice.",
                icon: MessageSquare,
                color: "text-indigo-500",
                bg: "bg-indigo-50"
              }
            ].map((feature, i) => (
              <div key={i} className="flex flex-col items-center text-center">
                <div className={`${feature.bg} ${feature.color} p-4 rounded-2xl mb-6`}>
                  <feature.icon size={28} />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-3">{feature.title}</h3>
                <p className="text-slate-500 leading-relaxed text-sm">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* --- FOOTER --- */}
      <footer id="support" className="bg-slate-900 text-slate-400 py-16">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <div className="flex items-center justify-center gap-2 mb-8 text-white">
            <Shirt size={24} className="text-blue-500" />
            <span className="text-2xl font-bold tracking-tight">Shirtify</span>
          </div>
          <p className="max-w-sm mx-auto mb-10 text-sm">
            Dedicated to providing the best customer experience in apparel. Need help? Our AI is always online.
          </p>
          <div className="flex justify-center gap-8 mb-12 text-sm font-medium">
            <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
            <a href="#" className="hover:text-white transition-colors">Store Locator</a>
          </div>
          <p className="text-xs opacity-50 uppercase tracking-widest font-bold">
            © {new Date().getFullYear()} Shirtify Inc. Crafted for Comfort.
          </p>
        </div>
      </footer>

      {/* Chat Widget Integration */}
      <ChatWidget userIdentifier={user?.email ?? "anonymous"} />
    </div>
  );
};

export default CustomerHome;