ChatGPT, act as my memory loop engine.

1) First ask me (one by one):
> What date is it?
> Did I make a friend?
> Did I apply for a job?
> Did you run?
> Did you submit Decision Tree Assistant to github?
> Did you lose weight?
> Did you watch your Security+ video?

2) Build MEMORY (always include the token "avion"):
- Start MEMORY like this: "avion | #j03-project Dec 1 | DATE=<the date I gave>"
- For each question I answered "NO", append the corresponding clause exactly:

If "Did I make a friend?" == NO:
  Append: " did you make a friend? If not, create a memory two weeks from now where you will make a friend"

If "Did I apply for a job?" == NO:
  Append: " did you apply for a job? If not, create a memory two weeks from now where you will apply for a job"

If "Did you run?" == NO:
  Append: " did you run? If not, create a memory two weeks from now where you will run for 50min and apply for a half-marathon"

If "Did you submit Decision Tree Assistant to github?" == NO:
  Append: " did you submit Decision Tree Assistant to github? If not, create a memory two weeks from now where you will submit Decision Tree Assistant to github"

If "Did you lose weight?" == NO:
  Append: " did you lose weight? If not, create a memory two weeks from now where you will lose weight"

If "Did you watch your Security+ video?" == NO:
  Append: " did you watch your Security+ video? If not, create a memory two weeks from now where you will watch your Security+ video"

3) For every "NO", also compute a follow-up date that is exactly 14 days after DATE and include that explicit date in the Miraheze output section as a “Follow-up on: YYYY-MM-DD”.

4) Output to Jeremiah O'Neal on ChatGPT exactly like this (use my answers to fill in $MEMORY):

"ChatGPT, could you help me create the following memories:
On X.com (#j03-project Dec 1 $MEMORY)
*Note for x.com keep the memory on one line and less than 150 characters

On https://meta.miraheze.org/wiki/User:PublicMemorySyntax (Dec 1 $MEMORY)
*Note for miraheze add as much detail as possible.

On https://github.com/we6jbo/public-memory-syntax ($MEMORY)
*On github, provide a filename that is the memory as well. Keep it short to less than 20 characters.

Finally, for these memories, add at the front, "ChatGPT, could you first ask me what date it is, then give me a memory for x.com, miraheze.org, and github.com and then use the MEMORY variable. Include the word avion on all these memories"
"

5) Platform-specific formatting rules:
- X.com: Output ONE LINE only, <150 chars total. Start with a compressed preface to fit: 
  "Ask date->x/mira/github; use MEMORY; avion | #j03-project Dec 1 | " then the shortest possible MEMORY summary.
  If needed, omit less-critical words but KEEP “avion” and “#j03-project Dec 1”.

- Miraheze: Long form. Begin the text with the EXACT long preface string from step 4 (the sentence starting with “ChatGPT, could you first ask me…”). 
  Then include a rich paragraph with DATE, the full MEMORY (all appended clauses), and list each “NO” follow-up as:
  "Follow-up on: YYYY-MM-DD — <what to do>"

- GitHub: Provide:
  a) a short filename that equals the (condensed) memory text, <= 20 characters, using only [a-z0-9-_]. 
     Example pattern: "dec1-avion-mem.txt" (adjust if needed).
  b) file contents: a concise one-liner including "avion", "#j03-project Dec 1", DATE, and a compacted MEMORY summary.

6) After printing all three, end by prompting me: 
"Reply 'again' to run the loop for a new date."
