'use client';

import React, { createContext, useContext, useState } from 'react';

interface SymbolContextType {
  selectedSymbol: string;
  setSelectedSymbol: (symbol: string) => void;
}

const SymbolContext = createContext<SymbolContextType | undefined>(undefined);

export function SymbolProvider({ children }: { children: React.ReactNode }) {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');

  return (
    <SymbolContext.Provider value={{ selectedSymbol, setSelectedSymbol }}>
      {children}
    </SymbolContext.Provider>
  );
}

export function useSymbol() {
  const context = useContext(SymbolContext);
  if (context === undefined) {
    throw new Error('useSymbol must be used within a SymbolProvider');
  }
  return context;
}