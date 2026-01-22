import sys



if __name__ == "__main__":
    
    sys.stdout.reconfigure(line_buffering=True)
    
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = "config.csv"
        

    from parse_papers import parse_papers
  
   
    parse_papers(config_file)
