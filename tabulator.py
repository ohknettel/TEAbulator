from types import NoneType
import polars as pl
import re
import classes
import math
import random
import os

GDOC_SPREADSHEET_PATTERN = re.compile(r"docs\.google\.com/spreadsheets/d/(.+)/\w+")
IGNORED_COLUMNS = ["suit", "timestamp", "username"] # The stuff found in Google forms (timestamp) and for vote verification purposes (suit/username)

def build_csv_url(url: str) -> str:
	'''
	Takes a Google Sheets spreadsheet link (https://docs.google.com/spreadsheets/d/.../edit...) and converts it into a downloadable CSV link.
	:param durl: The Google Sheets document link.
	:returns: The exported CSV download link.
	'''

	document_id = re.search(GDOC_SPREADSHEET_PATTERN, url)
	if not document_id:
		raise ValueError("Invalid document link provided")

	return f"https://docs.google.com/spreadsheets/d/{document_id.group(1)}/export?format=csv"

def compute_n(ballots: list[classes.Ballot], quota: float, epilson=1e-6):
	'''
	Computes n such that the sum of min(w, n) for all ballots in a list is equal to one quota, where w is the weight of each ballot.
	:param ballots: The set of ballots.
	:param quota: The value of one quota.
	:param epilson: The degree of accuracy in finding n.
	'''

	low = 0.0
	high = quota

	while (high - low) >= epilson:
		n = (high + low) / 2
		wsum = sum([min(n, b.weight) for b in ballots])
		if wsum < quota:
			low = n
		else:
			high = n

	return (high + low) / 2

# Tie breaking functions
def break_wsum_threshold(candidates: list[classes.Candidate], threshold: int):
	'''
	Breaks between 2 or more canidates in terms of the largest total ballot weight a candidate has, where the ballots are above or equal to a threshold.
	:param candidates: The list of candidates.
	:param threshold: A specified threshold.
	:returns: The succeeding candidate, or a list of candidates if tie-breaking between said candidates has failed.
	'''

	within_threshold = [[b for (b, s) in c.ballots if s >= threshold] for c in candidates]
	find_sum = lambda l: sum([b.weight for b in l])
	maxsum = max(within_threshold, key=find_sum)
	dupl = [candidates[i] for i, l in enumerate(within_threshold) if find_sum(l) == find_sum(maxsum)]
	return dupl[0] if len(dupl) <= 1 else dupl

def break_weighted_scores(candidates: list[classes.Candidate], _):
	'''
	Breaks between 2 or more canidates in terms of the greatest sum of weighted scores a candidate has.
	:param candidates: The list of candidates.
	:param _: Parity argument, ignore
	:returns: The succeeding candidate, or a list of candidates if tie-breaking between said candidates has failed.
	'''

	find_wscore_sum = lambda c: sum([b.weight * s for (b, s) in c.ballots])
	max_wscore_sum = max(candidates, key=find_wscore_sum)
	dupl = [candidate for candidate in candidates if find_wscore_sum(candidate) == find_wscore_sum(max_wscore_sum)]
	return dupl[0] if len(dupl) <= 1 else dupl

def break_unweighted_scores(candidates: list[classes.Candidate], _):
	'''
	Breaks between 2 or more canidates in terms of the greatest sum of unweighted scores a candidate has.
	:param candidates: The list of candidates.
	:param _: Parity argument, ignore
	:returns: The succeeding candidate, or a list of candidates if tie-breaking between said candidates has failed.
	'''

	find_uscore_sum = lambda c: sum([s for (_, s) in c.ballots])
	max_uscore_sum = max(candidates, key=find_uscore_sum)
	dupl = [candidate for candidate in candidates if find_uscore_sum(candidate) == find_uscore_sum(max_uscore_sum)]
	return dupl[0] if len(dupl) <= 1 else dupl

def validate_csv(file_or_url: str):
	'''
	Validates whether the given file or URL is a proper TEA ballots spreadsheet.
	:param file_or_url: The filename or CSV file URL of the spreadsheet.
	:returns: The given `file_or_url` value if valid.
	'''

	if not os.path.exists(file_or_url) and not re.search(GDOC_SPREADSHEET_PATTERN, file_or_url):
		raise FileNotFoundError(f"Invalid spreadsheet file or URL: {file_or_url}")
	elif re.search(GDOC_SPREADSHEET_PATTERN, file_or_url):
		file_or_url = build_csv_url(file_or_url)

	df = pl.read_csv(file_or_url)
	if len(df.columns) <= 1:
		raise ValueError("Less than or 1 candidate(s) found")

	df = df.select(col for col in df.iter_columns() if not any(w in col.name.lower() for w in IGNORED_COLUMNS))
	for rind, row in enumerate(df.iter_rows(), start=1):
		for cind, item in enumerate(row, start=1):
			if type(item) not in [NoneType, int]:
				raise ValueError(f"Value of unrecognized type found: {item} (row {rind}, column {cind})")
			elif item and item > 5:
				raise ValueError(f"Integer outside 0-5 range found: {item} (row {rind}, column {cind})")

	del df
	return file_or_url

def tabulate(file_or_url: str):
	'''
	The meat and potatoes of this whole file, the tabulator
	:param file_or_url: The filename or CSV file URL of the spreadsheet.
	:returns: A dictionary with `"rounds"`: a list of tabulation rounds, `"quota"`: the quota of the election and `"seats"`: how many seats there will be in the election based on the number of ballots.
	'''

	file_or_url = validate_csv(file_or_url)
	
	df = pl.read_csv(file_or_url)
	df = df.select(col for col in df.iter_columns() if not any(w in col.name.lower() for w in IGNORED_COLUMNS))

	central_ballots: list[classes.Ballot] = []
	candidates: list[classes.Candidate] = []

	elected = []
	threshold = 5

	for row in df.iter_rows():
		central_ballots.append(classes.Ballot(weight=1.0, scores=list(row)))

	for i, col in enumerate(df.iter_columns()):
		candidate = classes.Candidate(col.name.encode("ascii", "ignore").decode("ascii")) # remove emojis and weird stuff, gonna render some candidates with []
		for ballot in central_ballots:
			score = ballot.scores[i] or 0
			candidate.ballots.append((ballot, score))
		candidates.append(candidate)

	def within_threshold() -> list[classes.Candidate]:
		within = []
		for candidate in candidates:
			if candidate in elected:
				continue

			ballot_thres = [b for (b, s) in candidate.ballots if s >= threshold]
			total_weight = sum(b.weight for b in ballot_thres)

			if total_weight >= quota:
				within.append(candidate)

		return within

	elected_seats = min(math.floor(3.5 + len(central_ballots) / 11), 40)
	quota = len(central_ballots) / elected_seats
	seats = elected_seats

	tie_breakers = [break_wsum_threshold, break_weighted_scores, break_unweighted_scores]
	rounds: list[classes.TabulationRound] = []

	zero_round = classes.TabulationRound()
	zero_round.weights = {c.name: float(sum([b.weight for (b, s) in c.ballots if s >= threshold])) for c in candidates}
	zero_round.unelected = candidates
	zero_round.threshold = 5

	rounds.append(zero_round)

	while threshold > 0:
		thresholded = within_threshold()
		
		while len(thresholded) > 0:
			cur_round = classes.TabulationRound()

			ballots = [[(b, s) for (b, s) in candidate.ballots if s >= threshold] for candidate in thresholded]
			ns = [(i, compute_n([b for (b, _) in b_set], quota)) for i, b_set in enumerate(ballots)]
			n = [(i, n) for (i, n) in ns if n == min(ns, key = lambda x: x[1])[1]]

			if len(n) > 1:
				tied = [thresholded[i] for (i, _) in n]
				i, n_val = random.choice(n)

				for breaker in tie_breakers:
					res = breaker(tied, threshold)
					if isinstance(res, list):
						tied = res
						continue
					else:
						i, n_val = next((i, val) for (i, val) in n if i == thresholded.index(res))
						break					
			else:
				i, n_val = n[0]

			weights = {c.name: float(sum([b.weight for (b, _) in ballots[i]])) for i, c in enumerate(thresholded)}
			weights.update({c.name: float(sum([b.weight for (b, s) in c.ballots if s >= threshold])) for c in candidates if c not in thresholded})
			cur_round.weights = weights

			reweighing = []
			candidate = thresholded[i]
			for (b, _) in ballots[i]:
				for ind, score in enumerate(b.scores):
					if ind != i and candidates[i] not in reweighing + elected:
						reweighing.append(candidates[i])

				b.weight -= min(b.weight, n_val)

			elected_seats -= 1
			if candidate not in elected:
				elected.append(candidate)

			cur_round.elected = candidate
			cur_round.unelected = [c for c in candidates if c not in elected]
			cur_round.threshold = threshold
			
			if len(reweighing) > 0:
				faux_round = classes.TabulationRound()
				faux_round.reweighing = reweighing
				faux_round.threshold = threshold
				faux_round.weights = weights
				rounds.append(faux_round)

			thresholded = within_threshold()
			rounds.append(cur_round)

		threshold -= 1

	non_elected = [c for c in candidates if c not in elected]
	if elected_seats > 0:
		while elected_seats > 0:
			cur_round = classes.TabulationRound()

			positive_ballots = [(i, [b for (b, s) in candidate.ballots if s > 0]) for i, candidate in enumerate(non_elected)]
			weights = [(i, sum([b.weight for b in ballots])) for (i, ballots) in positive_ballots]
			weight = [i for (i, w) in weights if w == max(weights, key = lambda p: p[1])[1]]

			if len(weight) > 1:
				tied = [non_elected[i] for i in weight]
				i = random.choice(weight)

				for breaker in tie_breakers:
					res = breaker(tied, threshold)
					if isinstance(res, list):
						tied = res
						continue
					else:
						i = next(i for i in weight if i == non_elected.index(res))
						break					
			else:
				i = weight[0]

			candidate = non_elected[i]
			_, ballots = positive_ballots[i]

			weights = {non_elected[i].name: _sum for (i, _sum) in weights}
			weights.update({c.name: float(sum([b.weight for (b, s) in c.ballots if s >= threshold])) for c in elected})
			cur_round.weights = weights

			reweighing = []
			for ballot in ballots:
				for ind, score in enumerate(ballot.scores):
					if ind != i and candidates[i] not in reweighing + elected:
						reweighing.append(candidates[i])
				ballot.weight = 0
			
			elected_seats -= 1
			if candidate not in elected:
				elected.append(candidate)

			non_elected = [c for c in candidates if c not in elected]

			cur_round.elected = candidate
			cur_round.unelected = non_elected
			cur_round.threshold = threshold
			cur_round.reweighing = reweighing

			rounds.append(cur_round)

	return {
		"rounds": rounds,
		"quota": quota,
		"seats": seats
	}

if __name__ == "__main__":
	file_or_url = input("Please enter a file path or a URL leading to a spreadsheet: ")
	try:
		file_or_url = validate_csv(file_or_url)
		data = tabulate(file_or_url)

		rounds = data.get("rounds")
		quota = data.get("quota")
		seats = data.get("seats")

		if not rounds:
			raise ValueError("Error in tabulation, consult developer")

		latest_round = rounds[-1]
		print(f"Quota = {quota or 0:.6f}, seats = {seats}")

		print(f"===== Elected =====")
		print("\n".join('- ' + _round.elected.name for _round in rounds if _round.elected != None))

		print(f"=== Disqualified ===")
		print("\n".join('- ' + candidate.name for candidate in latest_round.unelected))

	except Exception as e:
		raise