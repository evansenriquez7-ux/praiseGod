core components:
    - comprehensive knowledge graph. Should map out progression of what a student needs to learn in order to pass state tests. Contains subdomain branches. Each node in the knowledge graph subdomain branches contains learning competencies.
        - based on matatag curriculum already downloaded
    - student focused. Student give basic info like age, grade, and interests. In addition to this, this app must gather as much information about the strengths and weaknesses of a student in their learning process in order to better serve the student educationally.
        - must be able to properly assess student's knowledge is within any given subdomain. must be able to identify what the student knows and doesnt know in order to present them the correct practice problems and tailor difficulty levels to the student. 
        - must properly identify when a student has mastered a learning competency and knowledge graph node and is ready to move on to the next node.
    - teaching content:
        - introductory content for each knowledge graph node, that prepares user for practice problems. This includes worked examples. Should include critical definitions and illustrative ascii art or images.
            - content available in perseus templates that are already downloaded
        - practice problem generation tailored for each learning competency
            - practice problems available in perseus templates that are already downloaded
            - create practice problem skeletons from matatag curriculum learning competencies. practice problems must contain difficulty dimensions that can be tailored to a students' strengths and weaknesses
        - vocab and cognitive capacity of teaching content must align with the progression of the corresponding subdomain branch. Vocab and cognitive capacity of all teaching content for a given learning competency must incorporate vocab and cognitive capability from all learning competencies prior to the current learning competency, but nothing at or after the current learning competency.
        - all teaching content is meant for billions of users. It wouldn't be feasible to have a llm agent produce the teaching content for each student at runtime. We must create templates that can automatically create original student tailored introductory content and practice problems. This should also incorporate all the information gathered during the student's learning process. minimal llm agent token usage, at most.
            - Solution: 
                - create a bank of 25 most used interests by students
                - distill introductory content into templates that can be automatically wrapped by
                - create a thorough set of practice problem skeletons that thoroughly address each learning competency. 
                - for as many skeletons as feasible, allow the skeletons to be automatically wrapped by the bank of student interests. must be automatically validated for 100% accuracy
                - regarding language, once skeletons are approved and validated, we will manually translate the skeletons and student interest wrapper into another skeleton file by language
                - if student interests don't fall into the student interest bank, an llm agent will be utilized at runtime to generate teaching content 
    - llm agent tutor for specific teaching content, while being student focused 
    
    ** pg and testing pipeline
    - creating this mastery education engine has been a nightmare. the intent was for an agent to read the matatag written learning competency and immediately create practice problem generators that specifically addressed them. 
    Requirements were:
    - add difficulty dimensions so we could adjust them to monitor and help the students' learning.
    - to create different contextual variants and formatters so that there would be variability to help the students learning. 
    However, when i asked the agents to build the pg pipeline, they made severe errors. For example: 
    1) no single source of truth, meaning they would generate problems for testing but it wouldnt be the same type of problems showing in the student portal. 
    2) hiding errors and bugs so everything appeared to be fully functional but wasnt 
    3) not properly testing the pg pipeline by lowering the standards of the testing pipeline to allow defects to be judged as "PASS" during the testing phase. 
    
    - there must be a contractual spec doc. An agent must use this doc to manually review lc pg and produce standardized artifacts that will be used programatically in the testing pipeline, to see if an lc pg is ready for deployment or what bugs need to be fixed. This spec doc must be tracked via git history to ensure that agents don't weaken standards of the spec doc to create artifacts that cheat the testing pipeline. This testing pipeline phase should test everything first then output the results. After analyzing the results of that phase round, the agent should determine the best approach for fixing the root issues until all issues are fixed. After fixes are complete, the testing phase should loop until there are no issues according to the spec doc. 
    - there must be programmatic testing of the lc pg's, including all allowed combinations of dd's, contextual variants, and visual formatters. This must thoroughly test whether everything is working correctly; but only to the point where an llm agent is required to manually review the logical validity of the pg output as a whole. The output of this testing phase should point out if an lc pg is preliminarily ready for deployment or what bugs need to be fixed. This testing pipeline phase should test everything first then output the results. After analyzing the results of that phase round, the agent should determine the best approach for fixing the root issues until all issues are fixed. This should also be done in accordance with a contractual spec doc with tracked git history to ensure agents dont weaken standards to cheat the testing pipeline. After fixes are complete, the testing phase should loop until there are no issues according to the spec doc.
    - we are trying to create the ideal contractual spec docs for 1) programattic testing phases and 2) llm agent manual review testing phases.
    - we want a thorough set of relevant dd's, contextual variants, and visual formatters to student learning and growth. If any item of these, dont significantly contribute to student learning and growth, they should not be included in the pg pipeline. Additionally, certain items of these must be feasible to test according to the contractual spec docs and testing pipeline. If a single item of these requires unjustifiable amount of code to properly test, then it shouldnt be included in the pg. 
    - we need to find the best combination of pg features and contractual testing that thoroughly addresses everything in the matatag curriculum and actually helps the student learn and grow in them, so that they can pass state tests.
    - additionally, we need to create a pg pipeline codebase that can be most effectively tested by the testing pipeline. the pg pipeline codebase must be structured in a way where it can be efficiently fixed according the testing pipeline results. previously, the issue is a convoluted codebase, and more than a single-source-of-truth where fixing one part of the codebase wasn't enough to address the root issue. 

