import pcbnew,sys
b=pcbnew.LoadBoard(sys.argv[1]); ids=set(sys.argv[2].split(",")); n=0
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in ids: b.Remove(t); n+=1
b.Save(sys.argv[1]); print(n)
