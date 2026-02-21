import React, { useState } from 'react';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, BarChart, Bar
} from 'recharts';

// Mock data for the financial app
const mockData = {
    accounts: [
        { id: 1, name: 'Main Checking', balance: 12450.00, type: 'checking', change: 2.5 },
        { id: 2, name: 'Savings Account', balance: 45230.00, type: 'savings', change: 8.2 },
        { id: 3, name: 'Investment Portfolio', balance: 128750.00, type: 'investment', change: -1.3 },
        { id: 4, name: 'Crypto Wallet', balance: 8750.00, type: 'crypto', change: 15.7 },
    ],
    transactions: [
        { id: 1, date: '2024-02-04', description: 'Salary Deposit', amount: 5500.00, category: 'Income', type: 'income' },
        { id: 2, date: '2024-02-03', description: 'Amazon Purchase', amount: -156.99, category: 'Shopping', type: 'expense' },
        { id: 3, date: '2024-02-02', description: 'Electric Bill', amount: -89.50, category: 'Utilities', type: 'expense' },
        { id: 4, date: '2024-02-01', description: 'Investment Return', amount: 342.00, category: 'Investment', type: 'income' },
        { id: 5, date: '2024-01-31', description: 'Grocery Store', amount: -124.80, category: 'Food', type: 'expense' },
        { id: 6, date: '2024-01-30', description: 'Freelance Payment', amount: 1200.00, category: 'Income', type: 'income' },
        { id: 7, date: '2024-01-29', description: 'Gas Station', amount: -45.00, category: 'Transport', type: 'expense' },
        { id: 8, date: '2024-01-28', description: 'Netflix Subscription', amount: -15.99, category: 'Entertainment', type: 'expense' },
    ],
    monthlyData: [
        { month: 'Aug', income: 6200, expenses: 3800 },
        { month: 'Sep', income: 5800, expenses: 4200 },
        { month: 'Oct', income: 7100, expenses: 3500 },
        { month: 'Nov', income: 6500, expenses: 4100 },
        { month: 'Dec', income: 8200, expenses: 5200 },
        { month: 'Jan', income: 6900, expenses: 3900 },
    ],
    expenseCategories: [
        { name: 'Food', value: 850, color: '#10b981' },
        { name: 'Transport', value: 320, color: '#3b82f6' },
        { name: 'Entertainment', value: 280, color: '#8b5cf6' },
        { name: 'Shopping', value: 520, color: '#f59e0b' },
        { name: 'Utilities', value: 380, color: '#ef4444' },
    ],
    budgets: [
        { category: 'Food', budget: 600, spent: 450 },
        { category: 'Shopping', budget: 400, spent: 380 },
        { category: 'Entertainment', budget: 200, spent: 180 },
        { category: 'Transport', budget: 300, spent: 250 },
    ],
};

const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    }).format(amount);
};

const FinancialDashboard: React.FC = () => {
    const [activeTab, setActiveTab] = useState('overview');

    return (
        <div className="min-h-screen bg-slate-900 text-white">
            {/* Navigation */}
            <nav className="bg-slate-800 border-b border-slate-700 px-6 py-4">
                <div className="max-w-7xl mx-auto flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-emerald-500 rounded-lg flex items-center justify-center">
                            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <span className="text-xl font-bold">FinanceFlow</span>
                    </div>
                    <div className="flex gap-1 bg-slate-700 rounded-lg p-1">
                        {['overview', 'transactions', 'budgets', 'investments'].map((tab) => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === tab
                                        ? 'bg-emerald-500 text-white'
                                        : 'text-slate-300 hover:text-white hover:bg-slate-600'
                                    }`}
                            >
                                {tab.charAt(0).toUpperCase() + tab.slice(1)}
                            </button>
                        ))}
                    </div>
                    <div className="flex items-center gap-4">
                        <button className="p-2 text-slate-400 hover:text-white transition-colors">
                            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                            </svg>
                        </button>
                        <div className="w-10 h-10 bg-slate-600 rounded-full flex items-center justify-center">
                            <span className="text-sm font-medium">JD</span>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto px-6 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">Welcome back, John</h1>
                    <p className="text-slate-400">Here's your financial overview for today</p>
                </div>

                {/* Account Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    {mockData.accounts.map((account) => (
                        <div key={account.id} className="bg-slate-800 rounded-xl p-6 border border-slate-700 hover:border-emerald-500/50 transition-colors">
                            <div className="flex justify-between items-start mb-4">
                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${account.type === 'checking' ? 'bg-blue-500/20 text-blue-400' :
                                        account.type === 'savings' ? 'bg-emerald-500/20 text-emerald-400' :
                                            account.type === 'investment' ? 'bg-purple-500/20 text-purple-400' :
                                                'bg-amber-500/20 text-amber-400'
                                    }`}>
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                                    </svg>
                                </div>
                                <span className={`text-sm font-medium ${account.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                    {account.change >= 0 ? '+' : ''}{account.change}%
                                </span>
                            </div>
                            <p className="text-slate-400 text-sm mb-1">{account.name}</p>
                            <p className="text-2xl font-bold">{formatCurrency(account.balance)}</p>
                        </div>
                    ))}
                </div>

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                    {/* Income vs Expenses Chart */}
                    <div className="lg:col-span-2 bg-slate-800 rounded-xl p-6 border border-slate-700">
                        <h3 className="text-lg font-semibold mb-6">Income vs Expenses</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <AreaChart data={mockData.monthlyData}>
                                <defs>
                                    <linearGradient id="incomeGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="expenseGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="month" stroke="#94a3b8" />
                                <YAxis stroke="#94a3b8" />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                                    formatter={(value: number) => formatCurrency(value)}
                                />
                                <Area type="monotone" dataKey="income" stroke="#10b981" fill="url(#incomeGradient)" strokeWidth={2} />
                                <Area type="monotone" dataKey="expenses" stroke="#ef4444" fill="url(#expenseGradient)" strokeWidth={2} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Expense Breakdown Pie Chart */}
                    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                        <h3 className="text-lg font-semibold mb-6">Expense Breakdown</h3>
                        <ResponsiveContainer width="100%" height={200}>
                            <PieChart>
                                <Pie
                                    data={mockData.expenseCategories}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {mockData.expenseCategories.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                                    formatter={(value: number) => formatCurrency(value)}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                        <div className="space-y-2 mt-4">
                            {mockData.expenseCategories.map((category) => (
                                <div key={category.name} className="flex items-center justify-between text-sm">
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: category.color }}></div>
                                        <span className="text-slate-300">{category.name}</span>
                                    </div>
                                    <span className="font-medium">{formatCurrency(category.value)}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Bottom Row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Recent Transactions */}
                    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-lg font-semibold">Recent Transactions</h3>
                            <button className="text-emerald-400 text-sm hover:underline">View All</button>
                        </div>
                        <div className="space-y-4">
                            {mockData.transactions.map((transaction) => (
                                <div key={transaction.id} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition-colors">
                                    <div className="flex items-center gap-4">
                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${transaction.type === 'income' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                                            }`}>
                                            {transaction.type === 'income' ? (
                                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                                                </svg>
                                            ) : (
                                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                                                </svg>
                                            )}
                                        </div>
                                        <div>
                                            <p className="font-medium">{transaction.description}</p>
                                            <p className="text-sm text-slate-400">{transaction.date} • {transaction.category}</p>
                                        </div>
                                    </div>
                                    <span className={`font-semibold ${transaction.amount >= 0 ? 'text-emerald-400' : 'text-white'}`}>
                                        {transaction.amount >= 0 ? '+' : ''}{formatCurrency(transaction.amount)}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Budget Progress */}
                    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-lg font-semibold">Budget Progress</h3>
                            <button className="text-emerald-400 text-sm hover:underline">Manage</button>
                        </div>
                        <div className="space-y-6">
                            {mockData.budgets.map((budget) => {
                                const percentage = Math.min((budget.spent / budget.budget) * 100, 100);
                                const isOverBudget = budget.spent > budget.budget;
                                return (
                                    <div key={budget.category}>
                                        <div className="flex justify-between items-center mb-2">
                                            <span className="font-medium">{budget.category}</span>
                                            <span className={`text-sm ${isOverBudget ? 'text-red-400' : 'text-slate-400'}`}>
                                                {formatCurrency(budget.spent)} / {formatCurrency(budget.budget)}
                                            </span>
                                        </div>
                                        <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full rounded-full transition-all ${percentage >= 90 ? 'bg-red-500' : percentage >= 70 ? 'bg-amber-500' : 'bg-emerald-500'
                                                    }`}
                                                style={{ width: `${percentage}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Quick Actions */}
                        <div className="mt-8 pt-6 border-t border-slate-700">
                            <h4 className="font-semibold mb-4">Quick Actions</h4>
                            <div className="grid grid-cols-2 gap-3">
                                <button className="flex items-center justify-center gap-2 p-4 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 rounded-lg transition-colors">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                                    </svg>
                                    Add Transaction
                                </button>
                                <button className="flex items-center justify-center gap-2 p-4 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg transition-colors">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                    </svg>
                                    View Reports
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default FinancialDashboard;
