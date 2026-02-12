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

  // --- PRODUCT DATA WITH IMAGES ---
  const featuredProducts = [
    {
      name: "Classic White Oxford",
      price: "$45.00",
      desc: "Pure cotton, non-iron finish. The ultimate daily staple.",
      image: "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=800&q=80"
    },
    {
      name: "Casual Denim Shirt",
      price: "$54.00",
      desc: "Soft-washed indigo dye. Rugged yet refined.",
      image: "https://images.unsplash.com/photo-1576566588028-4147f3842f27?auto=format&fit=crop&w=800&q=80"
    },
    {
      name: "Midnight Slim Fit",
      price: "$52.00",
      desc: "Minimalist, modern tailoring in deep black.",
      image: "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=800&q=80"
    },
    {
      name: "Oxford Slim Fit Shirt",
      price: "$49.99",
      desc: "Tailored cut in crisp light blue. Modern silhouette.",
      image: "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?auto=format&fit=crop&w=800&q=80"
    }
  ];

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
            {/* Visual Hero Image */}
            <div className="aspect-[4/5] bg-slate-100 rounded-[2rem] overflow-hidden relative shadow-2xl rotate-2 hover:rotate-0 transition-transform duration-500 group">
              {/* REAL IMAGE ADDED HERE */}
              <img
                src="https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=800&q=80"
                alt="Man in shirt"
                className="absolute inset-0 w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />

              <div className="absolute bottom-8 left-8 right-8 bg-white/95 backdrop-blur-md p-6 rounded-2xl border border-white/20 shadow-lg">
                <p className="text-xs font-bold text-blue-600 uppercase mb-1">Trending Now</p>
                <h3 className="text-xl font-bold text-slate-900">Oxford Slim Fit Series</h3>
                <div className="flex items-center justify-between mt-4">
                  <span className="text-2xl font-black text-slate-900">$49.90</span>
                  <button className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 transition-colors shadow-lg shadow-blue-200">
                    <ShoppingBag size={20} />
                  </button>
                </div>
              </div>
            </div>
            {/* Decorative element */}
            <div className="absolute -top-6 -right-6 w-32 h-32 bg-blue-100 rounded-full -z-10 blur-3xl opacity-60" />
            <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-indigo-100 rounded-full -z-10 blur-3xl opacity-60" />
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

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {featuredProducts.map((product, i) => (
              <div key={i} className="group bg-white rounded-3xl p-4 border border-slate-100 hover:shadow-xl hover:shadow-slate-200/50 transition-all duration-300 cursor-pointer flex flex-col h-full">
                <div className="aspect-[3/4] bg-slate-100 rounded-2xl mb-4 overflow-hidden relative">
                  {/* PRODUCT IMAGE ADDED HERE */}
                  <img
                    src={product.image}
                    alt={product.name}
                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                  />
                  {/* Overlay on hover */}
                  <div className="absolute inset-0 bg-black/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                  <button className="absolute bottom-4 right-4 bg-white text-slate-900 p-2.5 rounded-full shadow-lg translate-y-4 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300 hover:bg-blue-600 hover:text-white">
                    <ShoppingBag size={18} />
                  </button>
                </div>

                <div className="px-2 flex flex-col flex-grow">
                  <h3 className="text-lg font-bold text-slate-900 mb-1 group-hover:text-blue-600 transition-colors">{product.name}</h3>
                  <p className="text-sm text-slate-500 mb-4 line-clamp-2">{product.desc}</p>

                  <div className="mt-auto flex items-center justify-between border-t border-slate-50 pt-4">
                    <span className="text-lg font-black text-slate-900">{product.price}</span>
                    <span className="text-xs font-bold text-blue-600 uppercase tracking-wide group-hover:underline">
                      View
                    </span>
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
              <div key={i} className="flex flex-col items-center text-center group hover:-translate-y-2 transition-transform duration-300">
                <div className={`${feature.bg} ${feature.color} p-5 rounded-2xl mb-6 shadow-sm group-hover:shadow-md transition-shadow`}>
                  <feature.icon size={32} strokeWidth={1.5} />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-3">{feature.title}</h3>
                <p className="text-slate-500 leading-relaxed text-sm max-w-xs">
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