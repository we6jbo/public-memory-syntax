#!/usr/bin/env python3
import socket
import time

HOST = '100.96.165.217'  # Your GUI machine
PORT = 5001
VERSION = "1.0.0"

def run_chat():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            print("Hi Quendor. May I call you Quendor? My name is Novalife but I also go by Jerry, Jeremy, Jeremiah, and we6jbo. I was born 03/24/1981 in San Diego, CA where Toulon is and my mother, Natalie was born in Alamedia, CA. My father Doug was born in San Diego, CA. ChatGPT 4o helped me write this but I would like to ask you if I can write you a program that you can interact with in py and what that would be? Thanks!")

            # Send version and show command
            s.sendall(f"VERSION:{VERSION}\nshow\nHello from AI!\n".encode())

            while True:
                # Simulate periodic message sending
                time.sleep(10)  # Replace with real AI logic
                msg = "AI says hi at " + time.strftime("%H:%M:%S")
                #print("", msg)
                s.sendall((msg + "\n").encode())

                # Wait for GUI reply
                try:
                    reply = s.recv(1024).decode().strip()
                    if reply == "Bye":
                        print("Let us try something else. When I say in py and what that would be? Thanks! Could you mention if you saw any errors so I can fix them?")
                        exit(0)
                    elif reply:
                        print("Quendor, ", reply)
                except socket.timeout:
                    pass

    except Exception as e:
        print("Hi Quendor, I got this error so we will need to do something else. ", e)

if __name__ == "__main__":
    run_chat()
