from dataclasses import dataclass, field

@dataclass
class UNE153010Config:
    COLORS: dict = field(default_factory=dict)

@dataclass
class UNE153020Config:
    COLORS: dict = field(default_factory=dict)