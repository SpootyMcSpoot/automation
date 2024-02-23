class Hospital:
    def food(): return 'gross'


class Patient:
    name = 'Bob'
    days = 3

    def escape(self):
        if Hospital.food() == 'gross':
            print(f"{self.name} hates the food!")
            self.days = max(0, self.days - 1)


p = Patient()
while p.days:
    print(f"{p.name} has {p.days} days left.")
    p.escape()

print(f"{p.name} escaped!")
