The NOVT team uses the following procedure for creating a software release when an update is needed:

    1. Make sure that your fork of the "master" branch is up-to-date
    2. Update appropriate version numbers in footprints.py and setup.py
    3. Update the release notes
    4. Open, review, and merge pull request with the release procedure changes
    5. Create a new tag/release on GitHub/GitLab
    6. Upload new version of software to PyPI

Detailed instructions for performing a release are given below:

1. Make sure that your fork of the "master" branch is up-to-date

Make sure that your fork of the "master" branch is up-to-date. One way to do this is by clicking the "Fetch 
Upsteam" button, and then "Fetch and merge". This branch should be used for the changes described in the rest of
this document.

2. Update the version number in footprints.py and setup.py

Update the VERSION variable in setup.py and the version listed in the docstring (code description) in 
footprints.py to the new version number, using the x.y.z convention (e.g. v0.4.1).

3. Update the release notes

In the docstring of footprints.py and CHANGES.md, write a concise but detailed description of all of the notable changes that have
occurred since the last release. One way to acquire this information is to scroll through the commit history of
the project, and look for commits in which a pull request was merged.

4. Open, review, and merge a pull request with the changes

Once you've committed the changes from (2) and (3) in your branch, push your branch to GitHub/GitLab using
the upstream remote, open a pull request that points to the "master" branch. Assign reviewers. Either you or the
reviewer should eventually merge this pull request.

5. Create a new tag/release on GitHub/GitLab

Once the pull request into the "master" branch from (4) has been merged, click on the "Releases" button on the
main page of the repository, then hit the "Draft a new release" button. The "Tag version" should be the version
number of the release, the "Target" should be the "master" branch, the "Release title" should (also) be the
version number of the release, and the "Description" should match that of the release notes entry in (3). Once all
of that information is added, hit the big green "Publish" release button.

6. Upload new version of software to PyPI

To upload the new tagged version of the software to PyPI, run the following:

- python setup.py sdist bdist_wheel
- twine upload -u '$<pypi_username>' -p '$<pypi_password>' --https://pypi.org/project/jwst-footprints/ https://upload.pypi.org/legacy/
  --skip-existing dist/*
