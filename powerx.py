import kivy
import RPi.GPIO as GPIO
import time

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty
from kivy.clock import Clock

plusButtonPinNum = 13
minusButtonPinNum = 15
buttonPinNum = 16
buzzerPinNum = 12

totalSeconds = 60
totalMilliseconds = totalSeconds * 1000
maxReps = 0
minWeight = 65
maxWeight = 700

def gpio_init():
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(buttonPinNum, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(plusButtonPinNum, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(minusButtonPinNum, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(buzzerPinNum, GPIO.OUT)


def formatTime(time): #time is in milliseconds
	minutes = int((time / (1000 * 60)) % 60)
	seconds = int((time / 1000) % 60)
	tenths = int((time % 1000) / 100)
	
	if time <= 60000:
		seconds = int(time / 1000)
		return "{0:02d}.{1}".format(seconds, tenths)
	else:
		return "{0}:{1:02d}".format(minutes, seconds)

class PowerXCounter(GridLayout):
	currentReps = 0
	totalTimeMilliseconds = totalMilliseconds
	prevBtnInput = 0

	#PROPERTIES
	timeRemaining = StringProperty(formatTime(totalTimeMilliseconds))
	counter = StringProperty("0")
	totalTons = StringProperty("0")
	weight = StringProperty(str(minWeight))

	def __init__(self, **kwargs):
		super(PowerXCounter, self).__init__(**kwargs)
		self.reset()
		Clock.schedule_interval(self.checkInput, 0.15)

	def reset(self):
		#GPIO / CLOCK RESET
		Clock.unschedule(self.timer)
		Clock.schedule_once(self.buzzeroff)

		#RESETS VARS	
		self.currentReps = 0
		self.totalTimeMilliseconds = totalMilliseconds
		self.prevBtnInput = GPIO.input(buttonPinNum)
		self.countdowninprogress = False
		self.countdownnum = 3
		self.buzzerlength = 1
		self.timerRunning = False

		#RESET LABELS
		self.counter = "0"
		self.timeRemaining = formatTime(totalMilliseconds)
		self.weight = str(minWeight)
		self.totalTons = "0"

	def checkInput(self, dt):
		#COUNTER BUTTON PRESS
		btnInput = GPIO.input(buttonPinNum)
		if btnInput != self.prevBtnInput:
			self.prevBtnInput = btnInput
			if not self.countdowninprogress:
				self.click()
		# +/- BUTTON PRESS
		if not self.timerRunning and not self.countdowninprogress and self.currentReps == 0:
			plusBtn = GPIO.input(plusButtonPinNum)
			minusBtn = GPIO.input(minusButtonPinNum)
			w = int(self.weight)
			if plusBtn and w < maxWeight:
				w += 5
			if minusBtn and w > minWeight:
				w -= 5
			self.weight = str(w)

	def countdown(self, dt):
		if self.countdownnum > 0:
			self.countdowninprogress = True
			self.totalTons = str(self.countdownnum)
			self.countdownnum -= 1
		else:
			self.totalTons = "GO!"
			self.countdowninprogress = False
			Clock.unschedule(self.countdown)
			Clock.schedule_once(self.buzzer)
			Clock.schedule_once(self.setnum, 0.3)
			Clock.schedule_interval(self.timer, 0.1)

	def setnum(self, dt):
		self.totalTons = "0"

	def settons(self):
		self.totalTons = str(self.currentReps * int(self.weight))

	def buzzeroff(self, dt):
		GPIO.output(buzzerPinNum, False)

	def buzzer(self, dt):
		GPIO.output(buzzerPinNum, True)			
		Clock.schedule_once(self.buzzeroff, self.buzzerlength)

	def click(self):
		if self.countdowninprogress:
			return

		if self.totalTimeMilliseconds == 0:
			self.reset()
		else:
			if self.currentReps == 0:
				Clock.schedule_interval(self.countdown, 0.5)
			elif self.currentReps < maxReps or maxReps == 0:
				self.counter = str(self.currentReps)
				self.settons()
			elif self.currentReps == maxReps:
				self.counter = str(maxReps)
				self.settons()
				Clock.unschedule(self.timer)
			else:
				self.reset()
				return

			self.currentReps += 1

	def timer(self, dt):
		self.totalTimeMilliseconds -= 100
		self.timerRunning = True
		self.timeRemaining = formatTime(self.totalTimeMilliseconds)
		if self.totalTimeMilliseconds == 0:
			Clock.unschedule(self.timer)
			self.buzzerlength = 3
			self.timerRunning = False
			Clock.schedule_once(self.buzzer)

class PowerXApp(App):
	def build(self):
		gpio_init()
		return PowerXCounter()
	
if __name__ == "__main__":
	PowerXApp().run()

GPIO.output(buzzerPinNum, False)
GPIO.cleanup()
