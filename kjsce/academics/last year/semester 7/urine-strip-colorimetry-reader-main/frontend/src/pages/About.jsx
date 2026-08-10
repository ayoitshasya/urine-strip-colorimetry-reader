export default function About() {
  return (
    <div className="page">
      <h1>About Colorimetry</h1>
      <p>
        Colorimetry is the science of measuring color to determine concentrations
        of chemical substances. Urine test strips contain reagent pads that
        change color when they react with specific compounds (glucose, protein,
        ketones, etc). By comparing the reacted color against a standard
        reference chart, we can estimate the concentration level.
      </p>
      <p>
        This tool automates that comparison using image processing: it extracts
        the average color of each pad and finds the closest match on a digital
        reference chart, removing subjectivity from manual visual reading.
      </p>
    </div>
  )
}