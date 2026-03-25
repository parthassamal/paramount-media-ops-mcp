import React, { useState } from "react";
import { Shield, Mail, Lock, User, ArrowRight, AlertCircle } from "lucide-react";

interface LoginScreenProps {
  onLogin: (user: { name: string; email: string }) => void;
  onNavigate: (page: string) => void;
}

type AuthMode = "login" | "signup" | "forgot";

export function LoginScreen({ onLogin, onNavigate }: LoginScreenProps) {
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleOAuthLogin = (provider: string) => {
    setLoading(true);
    setError("");
    
    // Simulate OAuth flow
    setTimeout(() => {
      setLoading(false);
      onLogin({
        name: "Demo User",
        email: `demo@${provider === "sso" ? "paramount.com" : `${provider}.com`}`,
      });
      onNavigate("dashboard");
    }, 1000);
  };

  const handleEmailLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email || !password) {
      setError("Please fill in all fields");
      return;
    }

    if (mode === "signup" && !name) {
      setError("Please enter your name");
      return;
    }

    setLoading(true);

    // Simulate login/signup
    setTimeout(() => {
      setLoading(false);
      
      // For demo, accept any @paramount.com email
      if (email.endsWith("@paramount.com") || mode === "signup") {
        onLogin({
          name: name || email.split("@")[0],
          email: email,
        });
        onNavigate("dashboard");
      } else {
        setError("Invalid credentials. Use @paramount.com email or sign up.");
      }
    }, 1000);
  };

  const handleForgotPassword = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email) {
      setError("Please enter your email");
      return;
    }

    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setError("");
      alert(`Password reset link sent to ${email}`);
      setMode("login");
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-[#0D1117] flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-[#0D1117] via-[#161B22] to-[#0D1117] p-12 flex-col justify-between relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#0064FF]/20 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-600/20 rounded-full blur-3xl" />
        </div>

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-12">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#0064FF] to-purple-600 flex items-center justify-center">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Paramount+</h1>
              <p className="text-sm text-slate-400">AI Operations Platform</p>
            </div>
          </div>

          <h2 className="text-4xl font-bold text-white mb-4">
            Intelligent Operations
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#0064FF] to-purple-500">
              Powered by AI
            </span>
          </h2>
          <p className="text-slate-400 text-lg max-w-md">
            Unified production issue tracking, streaming quality monitoring, and AI-powered root cause analysis.
          </p>
        </div>

        <div className="relative z-10 space-y-4">
          <div className="flex items-center gap-4 text-slate-400">
            <div className="w-10 h-10 rounded-lg bg-slate-800/50 flex items-center justify-center">
              <span className="text-2xl">🎬</span>
            </div>
            <div>
              <p className="text-white font-medium">67.5M+ Subscribers</p>
              <p className="text-sm">Monitored in real-time</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-slate-400">
            <div className="w-10 h-10 rounded-lg bg-slate-800/50 flex items-center justify-center">
              <span className="text-2xl">⚡</span>
            </div>
            <div>
              <p className="text-white font-medium">50% Faster MTTR</p>
              <p className="text-sm">With AI-powered RCA pipeline</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Auth Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center gap-3 mb-8 justify-center">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#0064FF] to-purple-600 flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Paramount+</h1>
              <p className="text-xs text-slate-400">AI Operations</p>
            </div>
          </div>

          <div className="bg-[#161B22] rounded-2xl border border-slate-800 p-8">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-white mb-2">
                {mode === "login" && "Welcome back"}
                {mode === "signup" && "Create account"}
                {mode === "forgot" && "Reset password"}
              </h2>
              <p className="text-slate-400">
                {mode === "login" && "Sign in to access the platform"}
                {mode === "signup" && "Get started with Paramount+ AI Ops"}
                {mode === "forgot" && "We'll send you a reset link"}
              </p>
            </div>

            {mode !== "forgot" && (
              <>
                {/* OAuth Providers */}
                <div className="space-y-3 mb-6">
                  <button
                    onClick={() => handleOAuthLogin("google")}
                    disabled={loading}
                    className="flex items-center justify-center gap-3 w-full py-3 px-4 bg-white hover:bg-gray-100 text-gray-800 rounded-xl font-medium transition-colors disabled:opacity-50"
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path
                        fill="#4285F4"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="#34A853"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="#FBBC05"
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      />
                      <path
                        fill="#EA4335"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      />
                    </svg>
                    Continue with Google
                  </button>

                  <button
                    onClick={() => handleOAuthLogin("apple")}
                    disabled={loading}
                    className="flex items-center justify-center gap-3 w-full py-3 px-4 bg-black hover:bg-gray-900 text-white rounded-xl font-medium transition-colors border border-slate-700 disabled:opacity-50"
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z" />
                    </svg>
                    Continue with Apple
                  </button>

                  <button
                    onClick={() => handleOAuthLogin("github")}
                    disabled={loading}
                    className="flex items-center justify-center gap-3 w-full py-3 px-4 bg-[#24292e] hover:bg-[#2f363d] text-white rounded-xl font-medium transition-colors disabled:opacity-50"
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                    </svg>
                    Continue with GitHub
                  </button>
                </div>

                {/* SSO Button */}
                <button
                  onClick={() => handleOAuthLogin("sso")}
                  disabled={loading}
                  className="flex items-center justify-center gap-3 w-full py-3 px-4 bg-gradient-to-r from-[#0064FF] to-purple-600 hover:from-[#0052CC] hover:to-purple-700 text-white rounded-xl font-medium transition-all disabled:opacity-50 mb-6"
                >
                  <Shield className="w-5 h-5" />
                  Continue with SSO
                </button>

                <div className="relative mb-6">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-slate-700"></div>
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-3 bg-[#161B22] text-slate-500">or continue with email</span>
                  </div>
                </div>
              </>
            )}

            {/* Email Form */}
            <form onSubmit={mode === "forgot" ? handleForgotPassword : handleEmailLogin}>
              {error && (
                <div className="flex items-center gap-2 p-3 mb-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {error}
                </div>
              )}

              {mode === "signup" && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-400 mb-2">Full Name</label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="John Doe"
                      className="w-full pl-10 pr-4 py-3 bg-[#0D1117] border border-slate-700 rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:border-[#0064FF] transition-colors"
                    />
                  </div>
                </div>
              )}

              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-400 mb-2">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@paramount.com"
                    className="w-full pl-10 pr-4 py-3 bg-[#0D1117] border border-slate-700 rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:border-[#0064FF] transition-colors"
                  />
                </div>
              </div>

              {mode !== "forgot" && (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-slate-400 mb-2">Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full pl-10 pr-4 py-3 bg-[#0D1117] border border-slate-700 rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:border-[#0064FF] transition-colors"
                    />
                  </div>
                </div>
              )}

              {mode === "login" && (
                <div className="flex justify-end mb-6">
                  <button
                    type="button"
                    onClick={() => setMode("forgot")}
                    className="text-sm text-[#0064FF] hover:underline"
                  >
                    Forgot password?
                  </button>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="flex items-center justify-center gap-2 w-full py-3 px-4 bg-slate-700 hover:bg-slate-600 text-white rounded-xl font-medium transition-colors disabled:opacity-50"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    {mode === "login" && "Sign in"}
                    {mode === "signup" && "Create account"}
                    {mode === "forgot" && "Send reset link"}
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            {/* Toggle Mode */}
            <div className="mt-6 text-center text-sm text-slate-400">
              {mode === "login" && (
                <>
                  Don't have an account?{" "}
                  <button
                    onClick={() => setMode("signup")}
                    className="text-[#0064FF] hover:underline font-medium"
                  >
                    Sign up
                  </button>
                </>
              )}
              {mode === "signup" && (
                <>
                  Already have an account?{" "}
                  <button
                    onClick={() => setMode("login")}
                    className="text-[#0064FF] hover:underline font-medium"
                  >
                    Sign in
                  </button>
                </>
              )}
              {mode === "forgot" && (
                <button
                  onClick={() => setMode("login")}
                  className="text-[#0064FF] hover:underline font-medium"
                >
                  Back to sign in
                </button>
              )}
            </div>

            {/* Domain verification note */}
            <div className="mt-6 p-3 bg-slate-800/50 rounded-lg">
              <p className="text-xs text-slate-500 text-center">
                SSO is available for <span className="text-slate-400">@paramount.com</span> email addresses.
                Contact IT if you need access.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
