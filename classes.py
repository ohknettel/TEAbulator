from dataclasses import dataclass, field

@dataclass
class Ballot:
	weight: float
	scores: list[int]
	timestamp: str | None = None

@dataclass
class Candidate:
	name: str
	ballots: list[tuple[Ballot, int]] = field(default_factory=list)

@dataclass
class FakeRegexResult:
	string: str

	def group(self, _: int):
		return self.string

class TabulationRound:
	_round: int
	elected: Candidate | None = None
	reweighing: list[Candidate] = []
	unelected: list[Candidate] = []
	threshold: int
	weights: dict[str, float]